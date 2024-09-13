"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/dev/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from app import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.login, name="login"),
    path("index", views.index, name="index"),
    path("criar_empresa", views.criacao_empresa, name='criar_empresa'),
    path("exibirempresa/<int:empresa_id>", views.exibir_empresa, name="exibirempresas"),
    path('empresas/<int:empresa_id>/update/', views.update_empresa, name="editar_empresa"),
    path('empresas/<int:empresa_id>/delete/', views.delete_empresa, name="deletar_empresa"),
    path("colaboradores", views.colaboradores, name="colaboradores"),
    path("logout", LogoutView.as_view(), name="logout"),
    path("historico-transacoes", views.transacoes, name="transacoes"),
    path("perfil/<int:user_id>", views.update_perfil, name="perfil"),
    path("tributos", views.tributos, name="tributos"),
    path("tributos/<int:tributo_id>/delete", views.excluir_tributo, name="delete_tributo"),
    path("fontes_receitas", views.fontes_receitas, name="fontes_receitas"),
    path("criterios/<int:tributo_id>", views.criterios, name="criterios"),
    path('criterios/<int:tributo_id>/delete/<int:criterio_id>/', views.deletar_criterio, name='delete_criterio'),
    path('criterios/<int:tributo_id>/update/<int:criterio_id>/', views.editar_criterio, name='update_criterio'),
    path("tributos/<int:tributo_id>/update", views.editar_tributo, name="update_tributo"),
    path("fontes_receitas/<int:fonte_receita_id>/delete", views.deletar_fontes_receitas, name="delete_fontes_receitas"),
    path("fontes_receitas/<int:fonte_receita_id>/update", views.editar_fontes_receitas, name="update_fontes_receitas"),
    path("transacoes/<int:empresa_id>", views.transacoes, name="transacoes"),
    path("transacoes/<int:empresa_id>/delete/<int:transacao_id>/", views.deletar_transacao, name="delete_transacao"),
    path("404", views.page_404, name="page_404"),
    path('users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    path('users/<int:user_id>/update/', views.update_user, name='update_user'),
    path('associacao_empresa_fonte_receita/<int:empresa_id>', views.AssociarEmpresaFonteReceita, name='ass_empresa_fonte_receita'),
    path('dissociacao_empresa_fonte_receita/<int:empresa_id>/fonte_receita/<int:fontereceita_id>', views.DissociarEmpresaFonteReceita, name='dis_empresa_fonte_receita'),
    path('associacao_empresa_tributo/<int:empresa_id>', views.AssociarEmpresaTributo, name='ass_empresa_tributo'),
    path('dissociacao_empresa_tributo/<int:empresa_id>/tributo/<int:tributo_id>', views.DissociarEmpresaTributo, name='dis_empresa_tributo'),
    path('adicionar_observcao/<int:empresa_id>', views.adicionarObservacao, name='adicionar_observacao'),
    path('deletar_observacao/<int:empresa_id>/<int:observacao_id>', views.deletarObservacao, name='deletar_observacao'),
    path('adicionar_historico/<int:empresa_id>', views.adicionarHistorico, name='adicionar_historico'),
    path('deletar_historico/<int:empresa_id>/<int:historico_id>', views.deletarHistorico, name='deletar_historico'),

]