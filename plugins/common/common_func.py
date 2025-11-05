def get_sftp():
    print('SFTP function called')

def regist(name,gender,*arg):
    print(f'이름: {name}, 성별: {gender}')
    print(f'기타옵션들: {arg}')    
    
def regist2(name,gender,*arg, **kwargs):
    print(f'이름: {name}, 성별: {gender}')
    print(f'기타옵션들: {arg}')
    email = kwargs.get['email'] or  'None'
    phone = kwargs.get['phone'] or  'None'

    if email:
        print(f'이메일: {email}')
    if phone:
        print(f'전화번호: {phone}')
