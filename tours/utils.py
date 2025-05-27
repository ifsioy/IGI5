def is_employee(user):
    return hasattr(user, 'employeeprofile')

def is_client(user):
    return hasattr(user, 'clientprofile')