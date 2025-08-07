from db import init_db, add_roll

con = init_db()

while True:
    val = int(input("DB에 업로드 할 주사위의 눈을 입력하세요(1~6, 다른 문자 입력 시 종료)"))
    if val >= 1 and val <= 6:
        add_roll(con, val)
    else:
        break

con.close()