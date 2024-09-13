from rolepermissions.roles import AbstractUserRole


class Administrador(AbstractUserRole):
    avaliable_permissions = {'ver_financeiro': True, 'adicionar_transacoes': True}


class Colaborador(AbstractUserRole):
    avaliable_permissions = {'ver_financeiro': False, 'adicionar_transacoes': False}
