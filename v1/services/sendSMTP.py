from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from ..config import config as cfg


def make(sender, receiver, title, content):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "%s"%(title)
    msg['From'] = sender
    msg['To'] = receiver
    html = MIMEText(content, 'html')
    msg.attach(html)
    return msg.as_string()

def template(payload):
    return '''
        <!DOCTYPE html>
        <html lang="en">
          <head>
            <meta charset="UTF-8" />
            <meta http-equiv="X-UA-Compatible" content="IE=edge" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <title>Document</title>
          </head>
          <body
            style="
              -webkit-user-select: none;
              -moz-user-select: none;
              -ms-user-select: none;
              user-select: none;
            "
          >
            <div
              style="
                width: 30%;
                min-width: 300px;
                padding: 80px;
                margin: 50px auto;
                text-align: center;
                align-items: center;
                justify-content: center;
              "
            >
              <img
                style="width: 50px; margin-bottom: 25px"
                src="https://cdn.discordapp.com/attachments/873888419972010034/887209876042940426/favicon.png"
                alt="logo"
              />
              <br />
              <div style="width: 100%; font-size: 24px; margin-bottom: 35px">
                공기, 공부를 기록하다
              </div>
              <br />
              <div style="font-size: 14px; margin-bottom: 90px">
                로그인을 하려면 이메일 인증을 해야합니다. 아래의 코드를 로그인 창에
                입력해주세요.
              </div>
              <div
                style="
                  width: 100%;
                  padding: 15px 0;
                  border: 1px solid #d9dfe5;
                  border-radius: 10px;
                  font-weight: bold;
                  background-color: #f8f8fa;
                  -webkit-user-select: text;
                  -moz-user-select: text;
                  -ms-user-select: text;
                  user-select: text;
                "
              >
                {email}
              </div>
            </div>
          </body>
        </html>
    '''.format(email=payload['authCode'])

def _send(receiver, title, payload):
    print(receiver, payload)
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.login(cfg.EMAIL_USER, cfg.EMAIL_PASSWORRD)

    html_message = template(payload)
    body = make(cfg.EMAIL_USER, receiver, title, html_message)

    server.sendmail(cfg.EMAIL_USER, receiver, body)
    server.quit()

    return True

def send(authcode, email):
    title = "[공기] 이메일 인증코드가 도착했습니다."
    payload = {"authCode": authcode}
    email_res = _send(email, title, payload)
    print(email_res)
