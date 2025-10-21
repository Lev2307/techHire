def generate_applicant_data(fn: str, ln: str, email: str, city: str, gender: str, age: int, exp: str, specs: list, techs: list, ps1: str, ps2: str):
    return {
        'first_name': fn,
        'last_name' : ln,
        'email': email,
        'city': city,
        'gender': gender,
        'age': age,
        'experience': exp,
        'specializations': specs,
        'technologies': techs,
        'password1': ps1,
        'password2': ps2
    }