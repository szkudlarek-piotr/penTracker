import os
import smtplib

import requests as re
import pymysql.cursors
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from email.message import EmailMessage

load_dotenv()
vintage_pens = "https://www.penrepairshop.com/pi-ra-vintage?sort=newest"

vintage_request = re.get(vintage_pens).text
vintage_soup = BeautifulSoup(vintage_request, features="html.parser")
product_list_section = vintage_soup.find("section", {"data-hook": "product-list"})
all_pens = product_list_section.find_all("li", {"data-hook": "product-list-grid-item"})

connection = pymysql.connect(host='localhost',
                             user=os.getenv("user_name"),
                             password=os.getenv("db_passwd"),
                             database=os.getenv("db_name"),
                             cursorclass=pymysql.cursors.DictCursor)

with connection:
    with connection.cursor() as cursor:
        for pen in all_pens:
            first_link = pen.find("a")["href"]
            pen_name = pen.find("p", {"class", "sxJv9vi oViQG_o---typography-11-runningText oViQG_o---priority-7-primary syHtuvM FzO_a9"}).text
            try:
                #this only works if the pen wasn't bought yet
                pen_price = pen.find("span", {"class", "cfpn1d"}).text
            except:
                #if the pen was sold
                pen_price = "Wyprzedane!"

            is_in_db_sql = """
            SELECT COUNT(*) 
            FROM `vintage_pens` 
            WHERE link LIKE %s
            """
            cursor.execute(is_in_db_sql, (first_link))
            db_count = list(cursor.fetchone().values())[0]
            if db_count > 0:
                print(f"Pióro {pen_name} jest już w bazie.")
            else:
                email_text = f"""Na stronie jest dostęne nowe pióro vintage! Oto jego parametry:
    nazwa: {pen_name.strip()},
    link: {first_link.strip()},
    cena: {pen_price.strip()}.
Pozdraiwam,
PSz"""

                msg = EmailMessage()
                msg['Subject'] = 'Nowe pióro dostęne!'
                msg['From'] = os.getenv("my_email")
                msg['To'] = os.getenv("pen_lover_email")
                msg.set_content(email_text)


                if pen_price != "Wyprzedane!":
                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                        smtp.login(os.getenv("my_email"), os.getenv("google_passwd"))
                        smtp.send_message(msg)

                    insert_sql = "INSERT INTO `vintage_pens` (`id`, `link`, `name`, `price`) VALUES (NULL, %s, %s, %s)"
                    cursor.execute(insert_sql, (first_link, pen_name, pen_price))
                    connection.commit()