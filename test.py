from bs4 import BeautifulSoup
import requests

url_link = "https://www.ncp.gov.sa/en/Pages/ProjectsInPipeline.aspx"
result = requests.get(url_link).text
doc = BeautifulSoup(result, "html.parser")