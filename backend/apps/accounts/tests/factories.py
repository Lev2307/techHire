from ..models import Specialization, Technology

def generate_specs(specs: list):
    genenerated_specs = []
    for s in specs:
        s = Specialization.objects.create(name=s)
        genenerated_specs.append(s)
    return [t.id for t in genenerated_specs]

def generate_techs(techs: list):
    genenerated_techs = []
    for s in techs:
        s = Technology.objects.create(name=s)
        genenerated_techs.append(s)
    return [t.id for t in genenerated_techs]

def generate_applicant_data(username: str, fn: str, email: str, city: str, exp: str, specs: list, techs: list, ps1: str, ps2: str):
    return {
        'username': username,
        'first_name': fn,
        'email': email,
        'city': city,
        'experience': exp,
        'specializations': specs,
        'technologies': techs,
        'password1': ps1,
        'password2': ps2
    }