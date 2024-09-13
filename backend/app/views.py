import random
from sqlite3 import IntegrityError
import random

from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login as login_django
from django.contrib.auth.decorators import login_required
from rolepermissions.roles import assign_role
from rolepermissions.decorators import has_role_decorator
from django.views.generic.edit import DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Empresa, Federal, Estadual, Municipal, EmpresaFonteReceita, FonteReceita, EmpresaTributo, Tributo, \
    EmpresaTransacoes
from django.db.models import Sum
from django.utils.timezone import now
from django.db.models.functions import TruncMonth
import json
from .models import Empresa, Federal, Estadual, Municipal, Tributo, FonteReceita, Vencimento, Criterios, \
    EmpresaFonteReceita, EmpresaTributo, CriterioAliquotas, EmpresaTransacoes, Transacoes, Observacoes, \
    EmpresaObservacao, \
    Historico, HistoricoEmpresa


@login_required(login_url="/")
def exibir_empresa(request, empresa_id):
    empresa = get_object_or_404(Empresa, id_empresa=empresa_id)

    # Recupera os IDs de CNPJ, IE e CCM da empresa
    cnpj = empresa.cnpj_federal.cnpj
    ie = empresa.ie_estadual.ie
    ccm = empresa.ccm_municipal.ccm

    # Recupera instâncias de Federal, Estadual e Municipal usando os IDs
    Cnpj = get_object_or_404(Federal, cnpj=cnpj)
    Ie = get_object_or_404(Estadual, ie=ie)
    Ccm = get_object_or_404(Municipal, ccm=ccm)

    # Fontes de Receita da Empresa
    empresa_fontesreceitas = EmpresaFonteReceita.objects.filter(id_empresa_empresa=empresa).select_related(
        'id_fonte_receita_fonte_receita')

    fontes_receitas = [efr.id_fonte_receita_fonte_receita for efr in empresa_fontesreceitas]

    # Tributos de uma empresa
    empresa_tributos = EmpresaTributo.objects.filter(id_empresa_empresa=empresa_id).select_related(
        'id_tributo_tributo'
    )
    tributos = [et.id_tributo_tributo for et in empresa_tributos]

    #Observações de uma empresa
    empresa_observacoes = EmpresaObservacao.objects.filter(id_empresa_empresa=empresa_id).select_related(
        'id_observacoes'
    )

    observacoes = [eo.id_observacoes for eo in empresa_observacoes]

    #Históricos de uma empresa
    empresa_historicos = HistoricoEmpresa.objects.filter(id_empresa_empresa=empresa_id).select_related(
        'id_historico'
    )

    historicos = [eh.id_historico for eh in empresa_historicos]

    # Transações de uma empresa
    empresa_transacoes = EmpresaTransacoes.objects.filter(id_empresa_empresa=empresa).select_related(
        'id_transacoes_transacoes')

    transacoes = [et.id_transacoes_transacoes.transacao for et in empresa_transacoes]
    sum_transacoes = sum(transacoes)

    n_empresa_fontes_receita = empresa_fontesreceitas.count()
    n_empresa_tributos = empresa_tributos.count()

    # Somatória das transações agrupadas por mês do ano corrente
    transacoes_por_mes = EmpresaTransacoes.objects.filter(
        id_empresa_empresa=empresa,
        id_transacoes_transacoes__data__year=now().year
    ).annotate(
        mes=TruncMonth('id_transacoes_transacoes__data')
    ).values('mes').annotate(
        total_transacoes=Sum('id_transacoes_transacoes__transacao')
    ).order_by('mes')

    # Preparar dados para o gráfico ApexCharts
    meses = [t['mes'].strftime('%Y-%m') for t in transacoes_por_mes]  # Formato 'YYYY-MM' para representar o mês
    total_transacoes = [float(t['total_transacoes']) for t in transacoes_por_mes]

    # Convertendo os dados para JSON
    data_for_chart = json.dumps({
        'categories': meses,
        'series': total_transacoes
    })

    contextos = calcular_tributo_empresa(empresa_id);

    return render(request, template_name="frontend/Empresa.html", context={
        "empresa": empresa,
        "tributos": tributos,
        "Ccm": Ccm,
        "Ie": Ie,
        "Cnpj": Cnpj,
        'fontes_receitas': fontes_receitas,
        'n_empresa_fontes_receita': n_empresa_fontes_receita,
        'n_empresa_tributos': n_empresa_tributos,
        'sum_transacoes': sum_transacoes,
        'data_for_chart': data_for_chart,  # Dados para o gráfico
        'contextos': contextos,
        'observacoes': observacoes,
        'historicos': historicos
    })


def login(request):
    if request.user.is_authenticated:
        # Se o usuário já estiver autenticado, redirecione para a página inicial
        return redirect('index')

    if request.method == "GET":
        return render(request, 'frontend/pages-login.html')
    else:
        username = request.POST.get('username')
        senha = request.POST.get('senha')
        user = authenticate(username=username, password=senha)
        if user:
            login_django(request, user)
            return redirect('index')
        return HttpResponse("Usuário ou senha inválidos")


@login_required(login_url="/")
def transacoes(request):
    return render(request, template_name="frontend/historico-transacoes.html")


@login_required(login_url="/")
@has_role_decorator('administrador')
def colaboradores(request):
    if request.method == "GET":
        users = User.objects.all()
        return render(request, 'frontend/pages-colaboradores.html', {'users': users})
    else:
        username = request.POST.get('username')
        email = request.POST.get('email')
        senha = request.POST.get('senha')
        grupo = request.POST.get('grupo')

        user = User.objects.filter(username=username).first()
        if user:
            return HttpResponse("Já existe um usuário com esse nome")

        # Cria o novo usuário
        user = User.objects.create_user(username=username, email=email, password=senha)

        # Verifica se o grupo existe, se não, cria-o
        group, created = Group.objects.get_or_create(name=grupo)
        user.groups.add(group)
        # Salva o usuário
        user.save()
        assign_role(user, grupo)
        users = User.objects.all()
        return render(request, 'frontend/pages-colaboradores.html', {'users': users})


@login_required(login_url="/")
def perfil(request):
    return render(request, template_name="frontend/page-perfil.html")


@login_required(login_url="/")
def page_404(request, exception):
    return render(request, "frontend/pages-404.html", {}, status=404)


def delete_user(request, user_id):
    context = {}
    usuario = get_object_or_404(User, id=user_id)
    context['object'] = usuario
    if request.method == "POST":
        usuario.delete()
        return redirect('colaboradores')
    return render(request, 'frontend/confirmar_excluir.html', context);


def update_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        senha = request.POST.get('senha')
        grupo = request.POST.get('grupo')

        try:
            # Atualiza os campos do usuário
            user.username = username
            user.email = email

            # Apenas atualize a senha se for fornecida
            if senha:
                user.senha = senha

            # Adiciona o usuário ao grupo especificado
            group, created = Group.objects.get_or_create(name=grupo)
            user.groups.add(group)

            user.save()
            assign_role(user, grupo)

            return redirect('colaboradores')
        except IntegrityError:
            # Caso haja uma violação da restrição UNIQUE
            print("Ocorreu o IntegrityError")
            return render(request, 'frontend/pages-colboradores.html', {
                'user': user,
                'error_message': 'Nome de usuário ou email já está em uso.'
            })

    return render(request, 'frontend/Editar_Usuario.html', {'user': user})


@login_required(login_url="/")
def criacao_empresa(request):
    if request.method == 'POST':
        try:
            # Criação das entidades
            federal = Federal.objects.create(
                cnpj=request.POST.get('cnpj_federal'),
                login_federal=request.POST.get('login_federal'),
                senha_federal=request.POST.get('senha_federal'),
                certificado_digital_federal=bool(request.POST.get('certificado_digital_federal'))
            )

            estadual = Estadual.objects.create(
                ie=request.POST.get('ie_estadual'),
                login_estadual=request.POST.get('login_estadual'),
                senha_estadual=request.POST.get('senha_estadual'),
                certificado_digital_estadual=bool(request.POST.get('certificado_digital_estadual'))
            )

            municipal = Municipal.objects.create(
                ccm=request.POST.get('ccm_municipal'),
                login_municipal=request.POST.get('login_municipal'),
                senha_municipal=request.POST.get('senha_municipal'),
                certificado_digital_municipal=bool(request.POST.get('certificado_digital_municipal'))
            )

            empresa = Empresa.objects.create(
                nome=request.POST.get('nome_empresa'),
                responsaveis=request.POST.get('responsaveis_empresa'),
                atividade=request.POST.get('atividade_empresa'),
                regime_apuracao=request.POST.get('regime_apuracao'),
                cnpj_federal=federal,
                ie_estadual=estadual,
                ccm_municipal=municipal,
            )

            print("A empresa e as entidades relacionadas foram cadastradas com sucesso")
            return redirect('index')

        except Exception as e:
            print(f"Ocorreu um erro: {str(e)}")
            return render(request, 'frontend/index.html', {'error_message': str(e)})

    return render(request, 'frontend/adicionar_empresa.html')


@login_required(login_url="/")
def update_empresa(request, empresa_id):
    empresa = get_object_or_404(Empresa, id_empresa=empresa_id)

    # Acessando os valores diretamente dos campos
    cnpj = empresa.cnpj_federal.cnpj
    ie = empresa.ie_estadual.ie
    ccm = empresa.ccm_municipal.ccm

    print(ccm)  # Retorna o valor do ccm
    print(cnpj)  # Retorna o valor do cnpj
    print(ie)  # Retorna o valor do ie

    # Recuperando as instâncias relacionadas
    Cnpj = get_object_or_404(Federal, cnpj=cnpj)
    Ie = get_object_or_404(Estadual, ie=ie)
    Ccm = get_object_or_404(Municipal, ccm=ccm)

    if request.method == "POST":
        try:
            # Atualizando os valores da instância Federal
            Cnpj.cnpj = request.POST.get('cnpj_federal')
            Cnpj.login_federal = request.POST.get('login_federal')
            Cnpj.senha_federal = request.POST.get('senha_federal')
            Cnpj.certificado_digital_federal = bool(request.POST.get('certificado_digital_federal'))
            Cnpj.save()

            # Atualizando os valores da instância Estadual
            Ie.ie = request.POST.get('ie_estadual')
            Ie.login_estadual = request.POST.get('login_estadual')
            Ie.senha_estadual = request.POST.get('senha_estadual')
            Ie.certificado_digital_estadual = bool(request.POST.get('certificado_digital_estadual'))
            Ie.save()

            # Atualizando os valores da instância Municipal
            Ccm.ccm = request.POST.get('ccm_municipal')
            Ccm.login_municipal = request.POST.get('login_municipal')
            Ccm.senha_municipal = request.POST.get('senha_municipal')
            Ccm.certificado_digital_municipal = bool(request.POST.get('certificado_digital_municipal'))
            Ccm.save()

            # Atualizando a instância Empresa
            empresa.nome = request.POST.get('nome_empresa')
            empresa.responsaveis = request.POST.get('responsaveis_empresa')
            empresa.atividade = request.POST.get('atividade_empresa')
            empresa.regime_apuracao = request.POST.get('regime_apuracao')
            empresa.cnpj_federal = Cnpj  # Atribuindo a instância, não apenas o valor do campo
            empresa.ccm_municipal = Ccm  # Atribuindo a instância, não apenas o valor do campo
            empresa.ie_estadual = Ie  # Atribuindo a instância, não apenas o valor do campo
            empresa.save()

            return redirect('index')
        except IntegrityError:
            print("Ocorreu o IntegrityError")

    return render(request, 'frontend/Editar_Empresa.html', {'empresa': empresa,
                                                            'municipal': Ccm,
                                                            'estadual': Ie,
                                                            'federal': Cnpj})


@login_required(login_url="/")
def delete_empresa(request, empresa_id):
    print("Função delete_empresa foi chamada.")
    empresa = get_object_or_404(Empresa, id_empresa=empresa_id)

    # Acessando os valores diretamente dos campos
    cnpj = empresa.cnpj_federal.cnpj
    ie = empresa.ie_estadual.ie
    ccm = empresa.ccm_municipal.ccm

    print(ccm)  # Retorna o valor do ccm
    print(cnpj)  # Retorna o valor do cnpj
    print(ie)  # Retorna o valor do ie

    # Recuperando as instâncias relacionadas
    Cnpj = get_object_or_404(Federal, cnpj=cnpj)
    Ie = get_object_or_404(Estadual, ie=ie)
    Ccm = get_object_or_404(Municipal, ccm=ccm)

    if request.method == 'POST':
        empresa.delete()
        Cnpj.delete()
        Ie.delete()
        Ccm.delete()
        return redirect('index')

    return render(request, 'frontend/excluir_empresa.html', {'empresa': empresa})


@login_required(login_url='/')
def update_perfil(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        senha = request.POST.get('senha')

        try:
            # Atualiza os campos do usuário
            user.username = username
            user.email = email

            # Apenas atualize a senha se for fornecida
            if senha:
                user.senha = senha

            user.save()

            return redirect('index')
        except IntegrityError:
            # Caso haja uma violação da restrição UNIQUE
            print("Ocorreu o IntegrityError")

    return render(request, 'frontend/page-perfil.html', {'user': user})


@login_required(login_url='/')
def tributos(request):
    tributos = Tributo.objects.all()

    if request.method == 'POST':
        # Coletando dados do formulário manualmente
        nome_tributo = request.POST.get('nome')
        fonte_receita_id = request.POST.get('fonte_receita')
        dia_vencimento = request.POST.get('dia')
        envio_email = request.POST.get('envio_email')
        confirmar_email = request.POST.get('confirmar_email')
        periodo_pagamento = request.POST.get('periodo_pagamento')
        deducao_imposto = request.POST.get('deducao_imposto')
        limite_superior = request.POST.get('limite_superior')
        limite_inferior = request.POST.get('limite_inferior')
        aliquota = request.POST.get('aliquota')

        # Criando Vencimento
        vencimento = Vencimento.objects.create(
            dia=dia_vencimento,
            periodo_pagamento=periodo_pagamento,
        )

        # Criando Criterios
        criterios = Criterios.objects.create(
            deducao_imposto=deducao_imposto,
            limite_superior=limite_superior,
            limite_inferior=limite_inferior,
            aliquota=aliquota
        )

        # Criando Tributo
        fonte_receita = FonteReceita.objects.get(id_fonte_receita=fonte_receita_id)
        tributo = Tributo.objects.create(
            nome=nome_tributo,
            envio_email=envio_email,
            confirmacao_email=confirmar_email,
            id_data_vencimento_vencimento_id=vencimento.id_data_vencimento,
            id_fonte_receita_fonte_receita_id=fonte_receita.id_fonte_receita,
        )

        # Criando CriterioAliquotas
        CriterioAliquotas.objects.create(
            id_aliquotas_criterios_id=criterios.id_aliquotas,
            id_tributo_tributo_id=tributo.id_tributo
        )

        return redirect('tributos')  # Redirecione para uma página de sucesso

    fontes_receitas = FonteReceita.objects.all()
    tributos_mensais = Tributo.objects.filter(id_data_vencimento_vencimento__periodo_pagamento="Mensal").count()
    tributos_trimestral = Tributo.objects.filter(id_data_vencimento_vencimento__periodo_pagamento="Trimestral").count()
    tributos_anual = Tributo.objects.filter(id_data_vencimento_vencimento__periodo_pagamento="anual").count()
    return render(request, 'frontend/tributos.html',
                  {
                      "fontes_receita": fontes_receitas,
                      "tributos": tributos,
                      "tributos_mensais": tributos_mensais,
                      "tributos_trimestral": tributos_trimestral,
                      "tributos_anual": tributos_anual
                  })


@login_required(login_url='/')
def excluir_tributo(request, tributo_id):
    context = {}
    tributo = get_object_or_404(Tributo, id_tributo=tributo_id)
    context['object'] = tributo
    if request.method == 'POST':
        tributo.delete()
        return redirect('tributos')
    return render(request, 'frontend/excluir_tributo.html', {'tributo': tributo});


@login_required(login_url='/')
def editar_tributo(request, tributo_id):
    tributo = get_object_or_404(Tributo, id_tributo=tributo_id)
    vencimento = get_object_or_404(Vencimento,
                                   id_data_vencimento=tributo.id_data_vencimento_vencimento.id_data_vencimento)
    fonte_receita = get_object_or_404(FonteReceita,
                                      id_fonte_receita=tributo.id_fonte_receita_fonte_receita.id_fonte_receita)

    if request.method == 'POST':
        # Coletando dados do formulário manualmente
        nome_tributo = request.POST.get('nome')
        periodo_pagamento = request.POST.get('periodo_pagamento')
        envio_email = request.POST.get('envio_email')
        confirmar_email = request.POST.get('confirmar_email')
        fonte_receita_id = request.POST.get('fonte_receita')
        dia_vencimento = request.POST.get('dia')

        vencimento.dia = dia_vencimento
        vencimento.periodo_pagamento = periodo_pagamento
        tributo.nome = nome_tributo
        tributo.envio_email = envio_email
        tributo.confirmacao_email = confirmar_email
        fonte_receita.nome = fonte_receita_id

        tributo.save()

        return redirect('tributos')

    fontes_receitas = FonteReceita.objects.all()
    return render(request, 'frontend/editar_tributo.html', {'tributo': tributo,
                                                            'fontes_receita': fontes_receitas})


@login_required(login_url='/')
def criterios(request, tributo_id):
    # Obtendo o tributo pelo id_tributo fornecido
    tributo = get_object_or_404(Tributo, id_tributo=tributo_id)

    # Função para criar um novo critério em relação a um tributo
    if request.method == 'POST':
        # Coletando dados do formulário
        deducao_imposto = request.POST.get('deducao_imposto')
        limite_superior = request.POST.get('limite_superior')
        limite_inferior = request.POST.get('limite_inferior')
        aliquota = request.POST.get('aliquota')

        # Criando um novo critério
        novo_criterio = Criterios.objects.create(
            deducao_imposto=deducao_imposto,
            limite_superior=limite_superior,
            limite_inferior=limite_inferior,
            aliquota=aliquota
        )

        # Relacionando o critério ao tributo
        CriterioAliquotas.objects.create(
            id_aliquotas_criterios=novo_criterio,  # Passando a instância de Criterios
            id_tributo_tributo=tributo  # Passando a instância de Tributo
        )

        # Redirecionando para a página de visualização de critérios
        return redirect('criterios', tributo_id=tributo.id_tributo)

    # Obtendo todos os CriterioAliquotas relacionados ao tributo
    criterio_aliquotas = CriterioAliquotas.objects.filter(id_tributo_tributo=tributo).select_related(
        'id_aliquotas_criterios')

    # Extraindo todos os critérios relacionados aos CriterioAliquotas
    criterios = [ca.id_aliquotas_criterios for ca in criterio_aliquotas]

    return render(request, 'frontend/criterios.html', {
        'tributo': tributo,
        'criterios': criterios
    })


@login_required(login_url='/')
def editar_criterio(request, tributo_id, criterio_id):
    # Obtendo o tributo pelo id_tributo fornecido
    tributo = get_object_or_404(Tributo, id_tributo=tributo_id)

    # Obtendo o critério pelo id_aliquotas fornecido
    criterio = get_object_or_404(Criterios, id_aliquotas=criterio_id)

    if request.method == 'POST':
        deducao_imposto = request.POST.get('deducao_imposto')
        limite_superior = request.POST.get('limite_superior')
        limite_inferior = request.POST.get('limite_inferior')
        aliquota = request.POST.get('aliquota')

        criterio.deducao_imposto = deducao_imposto
        criterio.limite_superior = limite_superior
        criterio.limite_inferior = limite_inferior
        criterio.aliquota = aliquota

        criterio.save()

        # Redirecionando para a página de visualização de critérios
        return redirect('criterios', tributo_id=tributo.id_tributo)

    return render(request, 'frontend/editar_criterio.html', {
        'tributo': tributo,
        'criterio': criterio
    })


@login_required(login_url='/')
def deletar_criterio(request, tributo_id, criterio_id):
    # Obtendo o tributo pelo id_tributo fornecido
    tributo = get_object_or_404(Tributo, id_tributo=tributo_id)

    # Obtendo o critério pelo id_aliquotas fornecido
    criterio = get_object_or_404(Criterios, id_aliquotas=criterio_id)

    # Verificando se o critério está relacionado ao tributo
    criterio_aliquota = get_object_or_404(CriterioAliquotas, id_aliquotas_criterios=criterio,
                                          id_tributo_tributo=tributo)

    if request.method == 'POST':
        # Deletando a relação entre o critério e o tributo
        criterio_aliquota.delete()

        # Opcional: Deletar o critério completamente se não estiver relacionado a outro tributo
        criterio.delete()

        # Redirecionando para a página de visualização de critérios
        return redirect('criterios', tributo_id=tributo.id_tributo)

    return render(request, 'frontend/excluir_criterio.html', {
        'tributo': tributo,
        'criterio': criterio
    })


@login_required(login_url='/')
def fontes_receitas(request):
    fonte_receitas = FonteReceita.objects.all()

    if request.method == 'POST':
        fonte_receita_nome = request.POST.get('fonte_receita')

        FonteReceita.objects.create(nome=fonte_receita_nome)

        return redirect('fontes_receitas')

    return render(request, 'frontend/fonte_receitas.html', {'fonte_receitas': fonte_receitas})


@login_required(login_url='/')
def editar_fontes_receitas(request, fonte_receita_id):
    fonte_receita = get_object_or_404(FonteReceita, id_fonte_receita=fonte_receita_id)

    if request.method == 'POST':
        fonte_receita_nome = request.POST.get('fonte_receita')

        fonte_receita.nome = fonte_receita_nome
        fonte_receita.save()

        return redirect('fontes_receitas')

    return render(request, 'frontend/editar_fonte_receita.html', {'fonte_receita': fonte_receita})


@login_required(login_url='/')
def deletar_fontes_receitas(request, fonte_receita_id):
    fonte_receita = get_object_or_404(FonteReceita, id_fonte_receita=fonte_receita_id)

    if request.method == 'POST':
        fonte_receita.delete()
        return redirect('fontes_receitas')

    return render(request, 'frontend/excluir_fonte_receita.html', {'fonte_receita': fonte_receita})


@login_required(login_url='/')
def transacoes(request, empresa_id):
    empresa = get_object_or_404(Empresa, id_empresa=empresa_id)

    if request.method == 'POST':
        data = request.POST.get('data')
        fonte_receita = request.POST.get('fonte_receita')
        valor = request.POST.get('valor')

        print(fonte_receita)

        # Criando um novo critério
        nova_transacao = Transacoes.objects.create(
            data=data,
            fonte_receita=fonte_receita,
            transacao=valor,
        )

        # Relacionando o critério ao tributo
        EmpresaTransacoes.objects.create(
            id_transacoes_transacoes=nova_transacao,  # Passando a instância de Criterios
            id_empresa_empresa=empresa  # Passando a instância de Tributo
        )

        return redirect('transacoes', empresa_id=empresa.id_empresa)

    # Obtendo todos os CriterioAliquotas relacionados ao tributo
    empresa_transacoes = EmpresaTransacoes.objects.filter(id_empresa_empresa=empresa).select_related(
        'id_transacoes_transacoes')

    # Extraindo todos os critérios relacionados aos CriterioAliquotas
    transacoes = [et.id_transacoes_transacoes for et in empresa_transacoes]

    fontes_receitas = FonteReceita.objects.filter(empresafontereceita__id_empresa_empresa=empresa)

    return render(request, 'frontend/historico-transacoes.html', {'transacoes': transacoes,
                                                                  'fontes_receitas': fontes_receitas,
                                                                  'empresa': empresa})


@login_required(login_url='/')
def deletar_transacao(request, empresa_id, transacao_id):
    # Obtendo o tributo pelo id_tributo fornecido
    empresa = get_object_or_404(Empresa, id_empresa=empresa_id)

    # Obtendo o critério pelo id_aliquotas fornecido
    transacao = get_object_or_404(Transacoes, id_transacoes=transacao_id)

    # Verificando se o critério está relacionado ao tributo
    empresa_transacao = get_object_or_404(EmpresaTransacoes, id_transacoes_transacoes=transacao,
                                          id_empresa_empresa=empresa)

    if request.method == 'POST':
        # Deletando a relação entre o critério e o tributo
        empresa_transacao.delete()

        # Opcional: Deletar o critério completamente se não estiver relacionado a outro tributo
        transacao.delete()

        # Redirecionando para a página de visualização de critérios
        return redirect('transacoes', empresa_id=empresa.id_empresa)

    return render(request, 'frontend/excluir_transacao.html', {
        'empresa': empresa,
        'transacao': transacao
    })


@login_required(login_url='/')
def AssociarEmpresaFonteReceita(request, empresa_id):
    empresa = get_object_or_404(Empresa, id_empresa=empresa_id)
    fontes_receitas = FonteReceita.objects.all()

    if request.method == 'POST':
        fonte_receita_id = request.POST.get('fonte_receita')
        fonte_receita = FonteReceita.objects.get(id_fonte_receita=fonte_receita_id)

        EmpresaFonteReceita.objects.create(
            id_empresa_empresa=empresa,
            id_fonte_receita_fonte_receita=fonte_receita,
        )

        return redirect('exibirempresas', empresa_id=empresa.id_empresa)

    return render(request, 'frontend/associar_empresa_fontereceita.html', {
        'fontes_receitas': fontes_receitas,
        'empresa': empresa
    })


@login_required(login_url='/')
def DissociarEmpresaFonteReceita(request, empresa_id, fontereceita_id):
    # Obtendo o tributo pelo id_tributo fornecido
    empresa = get_object_or_404(Empresa, id_empresa=empresa_id)

    # Obtendo o critério pelo id_aliquotas fornecido
    fonte_receita = get_object_or_404(FonteReceita, id_fonte_receita=fontereceita_id)

    # Verificando se o critério está relacionado ao tributo
    empresa_fontereceita = get_object_or_404(EmpresaFonteReceita, id_empresa_empresa=empresa,
                                             id_fonte_receita_fonte_receita=fonte_receita)

    if request.method == 'POST':
        # Deletando a relação entre o critério e o tributo
        empresa_fontereceita.delete()

        # Redirecionando para a página de visualização de critérios
        return redirect('exibirempresas', empresa_id=empresa.id_empresa)

    return render(request, 'frontend/des_empresa_fontereceita.html', {
        'fonte_receita': fonte_receita,
        'empresa': empresa
    })


@login_required(login_url='/')
def AssociarEmpresaTributo(request, empresa_id):
    empresa = get_object_or_404(Empresa, id_empresa=empresa_id)
    tributos = Tributo.objects.all()

    if request.method == 'POST':
        tributo_id = request.POST.get('tributo')
        tributo = Tributo.objects.get(id_tributo=tributo_id)

        EmpresaTributo.objects.create(
            id_empresa_empresa=empresa,
            id_tributo_tributo=tributo,
        )

        return redirect('exibirempresas', empresa_id=empresa.id_empresa)

    return render(request, 'frontend/associar_empresa_tributo.html', {
        'tributos': tributos,
        'empresa': empresa
    })


@login_required(login_url='/')
def DissociarEmpresaTributo(request, empresa_id, tributo_id):
    # Obtendo o tributo pelo id_tributo fornecido
    empresa = get_object_or_404(Empresa, id_empresa=empresa_id)

    # Obtendo o critério pelo id_aliquotas fornecido
    tributo = get_object_or_404(Tributo, id_tributo=tributo_id)

    # Verificando se o critério está relacionado ao tributo
    empresa_tributo = get_object_or_404(EmpresaTributo, id_empresa_empresa=empresa,
                                        id_tributo_tributo=tributo)

    if request.method == 'POST':
        # Deletando a relação entre o critério e o tributo
        empresa_tributo.delete()

        # Redirecionando para a página de visualização de critérios
        return redirect('exibirempresas', empresa_id=empresa.id_empresa)

    return render(request, 'frontend/des_empresa_fontereceita.html', {
        'tributo': tributo,
        'empresa': empresa
    })


def index(request):
    nome = request.GET.get('nome')
    atividade = request.GET.get('atividade')
    responsavel = request.GET.get('responsavel')
    regime_apuracao = request.GET.get('regime_apuracao')

    empresas_lucro_real = Empresa.objects.filter(regime_apuracao='Lucro Real').count()
    empresas_simples_nacional = Empresa.objects.filter(regime_apuracao='Simples Nacional').count()
    empresas_lucro_presumido = Empresa.objects.filter(regime_apuracao='Lucro Presumido').count()

    # Inicializa a queryset com todas as empresas
    empresas = Empresa.objects.all()

    # Aplicando os filtros
    if nome:
        empresas = empresas.filter(nome__icontains=nome)

    if atividade:
        empresas = empresas.filter(atividade__icontains=atividade)

    if responsavel:
        empresas = empresas.filter(responsavel__icontains=responsavel)

    if regime_apuracao:
        empresas = empresas.filter(regime_apuracao=regime_apuracao)

    return render(request, 'frontend/index.html', {
        'empresas': empresas,
        'empresas_lucro_real': empresas_lucro_real,
        'empresas_simples_nacional': empresas_simples_nacional,
        'empresas_lucro_presumido': empresas_lucro_presumido
    })


def calcular_tributo_empresa(empresa_id):
    # Recuperar a empresa pelo ID
    empresa = get_object_or_404(Empresa, id_empresa=empresa_id)

    # Pegar todas as transações da empresa
    transacoes = Transacoes.objects.filter(empresatransacoes__id_empresa_empresa=empresa)

    tributo_contexts = []  # Lista para armazenar os dados de cada tributo
    detalhes_gerais = []  # Lista para armazenar os detalhes de todas as transações
    total_imposto_geral = 0
    total_deducao_geral = 0

    # Iterar sobre todos os tributos relacionados à empresa
    empresa_tributos = EmpresaTributo.objects.filter(id_empresa_empresa=empresa)

    for empresa_tributo in empresa_tributos:
        tributo = empresa_tributo.id_tributo_tributo

        # Inicializar totais por tributo
        total_imposto = 0
        total_deducao = 0
        detalhes = []

        # Iterar sobre todas as transações da empresa
        for transacao in transacoes:
            fonte_receita = transacao.fonte_receita
            valor_transacao = transacao.transacao

            # Verificar se a fonte de receita da transação coincide com o tributo
            if tributo.id_fonte_receita_fonte_receita.nome == fonte_receita:

                # Pegar todos os critérios de alíquota associados ao tributo que se aplicam ao valor da transação
                criterios_aliquota = CriterioAliquotas.objects.filter(
                    id_tributo_tributo=tributo,
                    id_aliquotas_criterios__limite_inferior__lte=valor_transacao,
                    id_aliquotas_criterios__limite_superior__gte=valor_transacao
                )

                # Iterar sobre todos os critérios aplicáveis
                for criterio_aliquota in criterios_aliquota:
                    aliquota = criterio_aliquota.id_aliquotas_criterios.aliquota / 100  # Dividir por 100 para obter a porcentagem
                    valor_calculado = valor_transacao * aliquota  # Calcular o valor baseado na alíquota

                    # Verificar se é imposto ou dedução
                    tipo = criterio_aliquota.id_aliquotas_criterios.deducao_imposto

                    if tipo == 'deducao':
                        total_deducao += valor_calculado
                    elif tipo == 'imposto':
                        total_imposto += valor_calculado

                    # Guardar os detalhes de cada transação e seus critérios aplicados
                    detalhes.append({
                        'transacao': transacao,
                        'tributo': tributo.nome,
                        'valor_calculado': valor_calculado,
                        'tipo': tipo,
                        'aliquota': criterio_aliquota.id_aliquotas_criterios.aliquota,
                        'limite_inferior': criterio_aliquota.id_aliquotas_criterios.limite_inferior,
                        'limite_superior': criterio_aliquota.id_aliquotas_criterios.limite_superior
                    })

        # Somatório dos valores de imposto e dedução por tributo
        total_a_pagar = total_imposto - total_deducao

        # Armazenar os dados para este tributo
        tributo_contexts.append({
            'tributo': tributo.nome,
            'detalhes': detalhes,
            'total_imposto': total_imposto,
            'total_deducao': total_deducao,
            'total_a_pagar': total_a_pagar,
        })

        # Adicionar os valores totais ao geral
        total_imposto_geral += total_imposto
        total_deducao_geral += total_deducao
        detalhes_gerais.extend(detalhes)

    total_a_pagar_geral = total_imposto_geral - total_deducao_geral

    context = {
        'empresa': empresa,
        'tributo_contexts': tributo_contexts,  # Contexto de cada tributo
        'detalhes_gerais': detalhes_gerais,  # Todos os detalhes de transações
        'total_imposto_geral': total_imposto_geral,
        'total_deducao_geral': total_deducao_geral,
        'total_a_pagar_geral': total_a_pagar_geral,
    }

    # Renderizar o template com os dados de todos os tributos e transações
    return context


@login_required(login_url='/')
def adicionarObservacao(request, empresa_id):
    empresa = get_object_or_404(Empresa, id_empresa=empresa_id)

    if request.method == 'POST':
        observacao = request.POST.get("observacao")

        # Criando um novo critério
        nova_observacao = Observacoes.objects.create(
            observacao=observacao
        )

        # Relacionando o critério ao tributo
        EmpresaObservacao.objects.create(
            id_observacoes=nova_observacao,  # Passando a instância de Criterios
            id_empresa_empresa=empresa  # Passando a instância de Tributo
        )

        return redirect('exibirempresas', empresa_id=empresa.id_empresa)

    return render(request, 'frontend/adicionar_observacao.html', {'empresa': empresa})


@login_required(login_url='/')
def deletarObservacao(request, empresa_id, observacao_id):
    # Obtendo o tributo pelo id_tributo fornecido
    empresa = get_object_or_404(Empresa, id_empresa=empresa_id)

    # Obtendo o critério pelo id_aliquotas fornecido
    observacao = get_object_or_404(Observacoes, id=observacao_id)

    # Verificando se o critério está relacionado ao tributo
    empresa_observacao = get_object_or_404(EmpresaObservacao, id_observacoes=observacao,
                                           id_empresa_empresa=empresa)

    if request.method == 'POST':
        # Deletando a relação entre o critério e o tributo
        empresa_observacao.delete()

        # Opcional: Deletar o critério completamente se não estiver relacionado a outro tributo
        observacao.delete()

        # Redirecionando para a página de visualização de critérios
        return redirect('exibirempresas', empresa_id=empresa.id_empresa)

    return render(request, 'frontend/deletar_observacao.html', {
        'empresa': empresa,
        'observacao': observacao
    })

@login_required(login_url='/')
def adicionarHistorico(request, empresa_id):
    empresa = get_object_or_404(Empresa, id_empresa=empresa_id)

    if request.method == 'POST':
        data = request.POST.get("data")
        informacao = request.POST.get("informacao")

        # Criando um novo critério
        novo_historico = Historico.objects.create(
            data=data,
            informacao=informacao
        )

        # Relacionando o critério ao tributo
        HistoricoEmpresa.objects.create(
            id_historico=novo_historico,  # Passando a instância de Criterios
            id_empresa_empresa=empresa  # Passando a instância de Tributo
        )

        return redirect('exibirempresas', empresa_id=empresa.id_empresa)

    return render(request, 'frontend/adicionar_historico.html', {'empresa': empresa})

@login_required(login_url='/')
def deletarHistorico(request, empresa_id, historico_id):
    # Obtendo o tributo pelo id_tributo fornecido
    empresa = get_object_or_404(Empresa, id_empresa=empresa_id)

    # Obtendo o critério pelo id_aliquotas fornecido
    historico = get_object_or_404(Historico, id=historico_id)

    # Verificando se o critério está relacionado ao tributo
    empresa_historico = get_object_or_404(HistoricoEmpresa, id_historico=historico,
                                           id_empresa_empresa=empresa)

    if request.method == 'POST':
        # Deletando a relação entre o critério e o tributo
        empresa_historico.delete()

        # Opcional: Deletar o critério completamente se não estiver relacionado a outro tributo
        historico.delete()

        # Redirecionando para a página de visualização de critérios
        return redirect('exibirempresas', empresa_id=empresa.id_empresa)

    return render(request, 'frontend/deletar_historico.html', {
        'empresa': empresa,
        'historico': historico
    })