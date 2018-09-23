from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import requests
import os
import time
import shutil
import json

class Scraper():
    def __init__(self):
        opts = Options()
        opts.set_headless()
        assert opts.headless
        self.browser = Firefox(options=opts)
        with open("conf.json") as f:
            self.mail_conf = json.load(f)

    def scrape(self):
        folder_name = "9gag_{}".format(int(time.time()))
        if not os.path.exists(folder_name):
            os.mkdir(folder_name)
        self.browser.get("https://9gag.com/")
        count = 10
        curr_offset = 0
        scroll = True
        while count and scroll:
            self.browser.execute_script("window.scrollTo(0, window.scrollY + 10000)")
            articles = self.browser.find_elements_by_tag_name("article")
            print (curr_offset, len(articles))
            if curr_offset >= len(articles):
                break
            for _ in articles:
                if curr_offset >= len(articles):
                    scroll = False
                    break
                article = articles[curr_offset]
                post_container = article.find_elements_by_class_name("post-container")[0]
                sources = post_container.find_elements_by_tag_name("source")
                vdo_source = ""
                img_source = ""
                if sources:
                    for source in sources:
                        if source.get_attribute("src").endswith(".mp4"):
                            vdo_source = source.get_attribute("src")
                else:
                    print ("img")
                    img_src = post_container.find_elements_by_tag_name("img")[0]
                    img_source = img_src.get_attribute("src")

                if vdo_source:
                    print (vdo_source)
                    self.save_vdo(vdo_source, folder_name)
                    print ("saved")
                else:
                    print (img_source)
                curr_offset += 1
            count -= 1
        self.browser.close()
        self.zip_folder(folder_name)
        print ("sending mail...")
        self.sendall(folder_name)

    def sendall(self, folder_name):
        addrs = self.mail_conf["to_addr"]
        for addr in addrs:
            print ("sending mail to {}".format(addr))
            self.sendmail(addr, self.mail_conf["subject"], self.mail_conf["body"], "./{}.zip".format(folder_name))

    def sendmail(self, to_addr, subject, body, path_to_attachment=None):
        msg = MIMEMultipart()
        msg['From'] = self.mail_conf["from_addr"]
        msg['To'] = to_addr
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
    
        if path_to_attachment != None:
            filename = path_to_attachment.split('/')[-1]
            attachment = open(path_to_attachment, "rb")
        
            part = MIMEBase('application', 'zip')
            part.set_payload((attachment).read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
             
            msg.attach(part)
    
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(self.mail_conf["from_addr"], self.mail_conf["password"])
        text = msg.as_string()
        server.sendmail(self.mail_conf["from_addr"], to_addr, text)
        server.quit()
        print ("Mail sent")

    def save_vdo(self, vdo, folder_name):
        vdo_name = vdo.split("/")[-1]
        r = requests.request("GET", vdo)
        with open("{}/{}".format(folder_name ,vdo_name), "wb") as f:
            f.write(r.content)

    def zip_folder(self, folder):
        shutil.make_archive(folder, 'zip', folder)
        shutil.rmtree(folder)

if __name__ == "__main__":
    scraper = Scraper()
    scraper.scrape()

