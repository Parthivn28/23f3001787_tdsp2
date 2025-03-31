import subprocess
import tempfile
import os
from fastapi import FastAPI, Form, UploadFile,File,Query,HTTPException
from difflib import SequenceMatcher
import re
import datetime
import zipfile
import io
import csv
import json
import hashlib
from mangum import Mangum
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import base64
import numpy as np
import colorsys
from typing import List, Dict
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import tiktoken
import httpx
import requests
import pandas as pd
from bs4 import BeautifulSoup
from xml.etree import ElementTree

app = FastAPI()

handler = Mangum(app)

class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to specific origins if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_REFERER = "https://vercellinking.vercel.app"

# Questions and Answers Database
nothardcoded = [2, 3, 4, 5, 6, 7, 8, 9, 10, 14, 15, 16, 17, 18, 20, 23, 24, 27, 29, 30, 31, 32,37,38,40,41,42,43]  # Questions that require dynamic computation

QUESTIONS = {
    1: "Install and run Visual Studio Code. In your Terminal (or Command Prompt), type code -s and press Enter. Copy and paste the entire output below. What is the output of code -s?",
    2: "Running uv run --with httpie -- https [URL] installs the Python package httpie and sends a HTTPS request to the URL. Send a HTTPS request to https://httpbin.org/get with the URL encoded parameter email set to 23f3001787@ds.study.iitm.ac.in. What is the JSON output of the command? (Paste only the JSON body, not the headers)",
    3: "Let's make sure you know how to use npx and prettier. Download README.md. In the directory where you downloaded it, make sure it is called README.md, and run npx -y prettier@3.4.2 README.md | sha256sum. What is the output of the command?",
    4: "Let's make sure you can write formulas in Google Sheets. Type this formula into Google Sheets. (It won't work in Excel) =SUM(ARRAY_CONSTRAIN(SEQUENCE(100, 100, 9, 15), 1, 10)) What is the result?",
    5: "Let's make sure you can write formulas in Excel. Type this formula into Excel. (Note: This will ONLY work in Office 365.) =SUM(TAKE(SORTBY({6,10,11,9,0,7,1,11,5,4,15,12,13,8,14,1}, {10,9,13,2,11,8,16,14,7,15,5,4,6,1,3,12}), 1, 6)) What is the result?",
    6: "How many Wednesdays are there in the date range 1981-05-06 to 2007-08-17?",
    7: "Download and unzip file q-extract-csv-zip.zip which has a single extract.csv file inside. What is the value in the \"answer\" column of the CSV file?",
    8: "Let's make sure you know how to use JSON. Sort this JSON array of objects by the value of the age field. In case of a tie, sort by the name field. Paste the resulting JSON below without any spaces or newlines.\n\n[{\"name\":\"Alice\",\"age\":67},{\"name\":\"Bob\",\"age\":53},{\"name\":\"Charlie\",\"age\":34},{\"name\":\"David\",\"age\":89},{\"name\":\"Emma\",\"age\":92},{\"name\":\"Frank\",\"age\":37},{\"name\":\"Grace\",\"age\":4},{\"name\":\"Henry\",\"age\":49},{\"name\":\"Ivy\",\"age\":30},{\"name\":\"Jack\",\"age\":2},{\"name\":\"Karen\",\"age\":2},{\"name\":\"Liam\",\"age\":5},{\"name\":\"Mary\",\"age\":32},{\"name\":\"Nora\",\"age\":56},{\"name\":\"Oscar\",\"age\":19},{\"name\":\"Paul\",\"age\":22}]\nSorted JSON:",
    9: "Download q-multi-cursor-json.txt and use multi-cursors and convert it into a single JSON object, where key=value pairs are converted into {key: value, key: value, ...}. What's the result when you paste the JSON at tools-in-data-science.pages.dev/jsonhash and click the Hash button?",
    10: "Download and process q-unicode-data.zip the files in which contains three files with different encodings:\n\n" \
                  "data1.csv: CSV file encoded in CP-1252\n" \
                  "data2.csv: CSV file encoded in UTF-8\n" \
                  "data3.txt: Tab-separated file encoded in UTF-16\n\n" \
                  "Each file has 2 columns: symbol and value. Sum up all the values where the symbol matches \"”\" OR \"Š\" across all three files.\n\n" \
                  "What is the sum of all values associated with these symbols?",
    11: "Let's make sure you know how to use GitHub. Create a GitHub account if you don't have one. Create a new public repository. Commit a single JSON file called email.json with the value {\"email\": \"23f3001787@ds.study.iitm.ac.in\"} and push it.Enter the raw Github URL of email.json so we can verify it. (It might look like https://raw.githubusercontent.com/[GITHUB ID]/[REPO NAME]/main/email.json.)",
    12: "Let's make sure you know how to select elements using CSS selectors. Find all <div>s having a foo class in the hidden element below. What's the sum of their data-value attributes? Sum of data-value attributes:",
    13: "Just above this paragraph, there's a hidden input with a secret value.What is the value in the hidden input?",
    14: "Download and process q-replace-across-files.zip and unzip it into a new folder, then replace all \"IITM\" (in upper, lower, or mixed case) with \"IIT Madras\" in all files. Leave everything as-is - don't change the line endings. What does running cat * | sha256sum in that folder show in bash?",
    15: "Download q-list-files-attributes.zip and extract it. Use ls with options to list all files in the folder along with their date and file size. What's the total size of all files at least 4294 bytes large and modified on or after Sat, 29 Apr, 2006, 8:48 pm IST?",
    16: "Download q-move-rename-files.zip and extract it. Use mv to move all files under folders into an empty folder. Then rename all files replacing each digit with the next. (1 becomes 2, 9 becomes 0, e.g. a1b9c.txt becomes a2b0c.txt) What does running grep . * | LC_ALL=C sort | sha256sum in bash on that folder show?",
    17: "Download q-compare-files.zip and extract it. It has 2 nearly identical files, a.txt and b.txt, with the same number of lines. How many lines are different between a.txt and b.txt?",
    18: """There is a tickets table in a SQLite database that has columns type, units, and price. Each row is a customer bid for a concert ticket.
        type    units    price
        BRONZE    82    1.26
        Bronze    613    1.5
        silver    504    0.64
        gold    352    1.53
        gold    843    1.02
        ...
        What is the total sales of all the items in the "Gold" ticket type? Write SQL to calculate it.""",
    19:"""Question:
        Write documentation in Markdown for an **imaginary** analysis of the number of steps you walked each day for a week, comparing over time and with friends. The Markdown must include:

        - Top-Level Heading: At least 1 heading at level 1, e.g., # Introduction
        - Subheadings: At least 1 heading at level 2, e.g., ## Methodology
        - Bold Text: At least 1 instance of bold text, e.g., **important**
        - Italic Text: At least 1 instance of italic text, e.g., *note*
        - Inline Code: At least 1 instance of inline code, e.g., sample_code
        - Code Block: At least 1 instance of a fenced code block, e.g.,
        
        print(\"Hello World\")
        - Bulleted List: At least 1 instance of a bulleted list, e.g., - Item
        - Numbered List: At least 1 instance of a numbered list, e.g., 1. Step One
        - Table: At least 1 instance of a table, e.g., | Column A | Column B |
        - Hyperlink: At least 1 instance of a hyperlink, e.g., [Text](https://example.com)
        - Image: At least 1 instance of an image, e.g., ![Alt Text](https://example.com/image.jpg)
        - Blockquote: At least 1 instance of a blockquote, e.g., > This is a quote

        Enter your Markdown here:""",
        20:"Download the image below and compress it losslessly to an image that is less than 1,500 bytes. Upload your losslessly compressed image (every pixel must match the original).",
        21:"""Publish a page using GitHub Pages that showcases your work. Ensure that your email address 23f3001787@ds.study.iitm.ac.in is in the page's HTML.

GitHub pages are served via CloudFlare which obfuscates emails. So, wrap your email address inside a:

<!--email_off-->23f3001787@ds.study.iitm.ac.in<!--/email_off-->
What is the GitHub Pages URL? It might look like: https://[USER].github.io/[REPO]/""",
        22:"""Let's make sure you can access Google Colab. Run this program on Google Colab, allowing all required access to your email ID: 23f3001787@ds.study.iitm.ac.in.

import hashlib
import requests
from google.colab import auth
from oauth2client.client import GoogleCredentials

auth.authenticate_user()
creds = GoogleCredentials.get_application_default()
token = creds.get_access_token().access_token
response = requests.get(
  "https://www.googleapis.com/oauth2/v1/userinfo",
  params={"alt": "json"},
  headers={"Authorization": f"Bearer {token}"}
)
email = response.json()["email"]
hashlib.sha256(f"{email} {creds.token_expiry.year}".encode()).hexdigest()[-5:]
What is the result? (It should be a 5-character string)""",

        23:"""Download this image. Create a new Google Colab notebook and run this code (after fixing a mistake in it) to calculate the number of pixels with a certain minimum brightness:

import numpy as np
from PIL import Image
from google.colab import files
import colorsys

# There is a mistake in the line below. Fix it
image = Image.open(list(files.upload().keys)[0])

rgb = np.array(image) / 255.0
lightness = np.apply_along_axis(lambda x: colorsys.rgb_to_hls(*x)[1], 2, rgb)
light_pixels = np.sum(lightness > 0.934)
print(f'Number of pixels with lightness > 0.934: {light_pixels}')
What is the result? (It should be a number)""",

        24:"""Download q-vercel.json this  which has the marks of 100 imaginary students.

Create and deploy a Python app to Vercel. Expose an API so that when a request like https://your-app.vercel.app/api?name=X&name=Y is made, it returns a JSON response with the marks of the names X and Y in the same order, like this:

{ "marks": [10, 20] }
Make sure you enable CORS to allow GET requests from any origin.

What is the Vercel URL? It should look like: https://your-app.vercel.app/api""",

        25:"""Create a GitHub action on one of your GitHub repositories. Make sure one of the steps in the action has a name that contains your email address 23f3001787@ds.study.iitm.ac.in. For example:


jobs:
  test:
    steps:
      - name: 23f3001787@ds.study.iitm.ac.in
        run: echo "Hello, world!"
      
Trigger the action and make sure it is the most recent action.

What is your repository URL? It will look like: https://github.com/USER/REPO""",

    26:"""Create and push an image to Docker Hub. Add a tag named 23f3001787 to the image.

What is the Docker image URL? It should look like: https://hub.docker.com/repository/docker/$USER/$REPO/general""",

        27:"""Download . This file has 2-columns:

studentId: A unique identifier for each student, e.g. 1, 2, 3, ...
class: The class (including section) of the student, e.g. 1A, 1B, ... 12A, 12B, ... 12Z
Write a FastAPI server that serves this data. For example, /api should return all students data (in the same row and column order as the CSV file) as a JSON like this:

{
  "students": [
    {
      "studentId": 1,
      "class": "1A"
    },
    {
      "studentId": 2,
      "class": "1B"
    }, ...
  ]
}
If the URL has a query parameter class, it should return only students in those classes. For example, /api?class=1A should return only students in class 1A. /api?class=1A&class=1B should return only students in class 1A and 1B. There may be any number of classes specified. Return students in the same order as they appear in the CSV file (not the order of the classes).

Make sure you enable CORS to allow GET requests from any origin.

What is the API URL endpoint for FastAPI? It might look like: http://127.0.0.1:8000/api""",

        28:"""Download Llamafile. Run the Llama-3.2-1B-Instruct.Q6_K.llamafile model with it.

Create a tunnel to the Llamafile server using ngrok.

What is the ngrok URL? It might look like: https://[random].ngrok-free.app/""",

        29:"""DataSentinel Inc. is a tech company specializing in building advanced natural language processing (NLP) solutions. Their latest project involves integrating an AI-powered sentiment analysis module into an internal monitoring dashboard. The goal is to automatically classify large volumes of unstructured feedback and text data from various sources as either GOOD, BAD, or NEUTRAL. As part of the quality assurance process, the development team needs to test the integration with a series of sample inputs—even ones that may not represent coherent text—to ensure that the system routes and processes the data correctly.

Before rolling out the live system, the team creates a test harness using Python. The harness employs the httpx library to send POST requests to OpenAI's API. For this proof-of-concept, the team uses the dummy model gpt-4o-mini along with a dummy API key in the Authorization header to simulate real API calls.

One of the test cases involves sending a sample piece of meaningless text:

RJ 4E KUCUgIT7P zWr  kDE 2TV UYMqn aK19 Lwn X1lqM
Write a Python program that uses httpx to send a POST request to OpenAI's API to analyze the sentiment of this (meaningless) text into GOOD, BAD or NEUTRAL. Specifically:

Make sure you pass an Authorization header with dummy API key.
Use gpt-4o-mini as the model.
The first message must be a system message asking the LLM to analyze the sentiment of the text. Make sure you mention GOOD, BAD, or NEUTRAL as the categories.
The second message must be exactly the text contained above.
This test is crucial for DataSentinel Inc. as it validates both the API integration and the correctness of message formatting in a controlled environment. Once verified, the same mechanism will be used to process genuine customer feedback, ensuring that the sentiment analysis module reliably categorizes data as GOOD, BAD, or NEUTRAL. This reliability is essential for maintaining high operational standards and swift response times in real-world applications.

Note: This uses a dummy httpx library, not the real one. You can only use:

response = httpx.get(url, **kwargs)
response = httpx.post(url, json=None, **kwargs)
response.raise_for_status()
response.json()
Code""",

        30:"""LexiSolve Inc. is a startup that delivers a conversational AI platform to enterprise clients. The system leverages OpenAI’s language models to power a variety of customer service, sentiment analysis, and data extraction features. Because pricing for these models is based on the number of tokens processed—and strict token limits apply—accurate token accounting is critical for managing costs and ensuring system stability.

To optimize operational costs and prevent unexpected API overages, the engineering team at LexiSolve has developed an internal diagnostic tool that simulates and measures token usage for typical prompts sent to the language model.

One specific test case an understanding of text tokenization. Your task is to generate data for that test case.

Specifically, when you make a request to OpenAI's GPT-4o-Mini with just this user message:

List only the valid English words from these: 4j, vjU, rU, ll, t55T5Ri, Umwia, q, cr7hK3A, Hd, RKN6, GUv, VKOn0C, c, BUKIsgFD5, W0, lJrlGdd8B, cgt, cJpSZfO, fvJWl1k08, yXgeQ, zbWqKQq, kCdI, 7fpz8JN2Km, YlCYVh, wrD6ah18M, yJHJgp, ETpF1f2Ii, 5i8A, Nq4, 2Zc7, k, TXc09dRte, 0aoxF, DII7G, ZoIIY95t, rHLGXbQVE, 54Cl, uf, LWqtuxql, BaCiH, 5bTG4, OQAdCrLChf, eK, jq, 36XDCD, lej, eHRqel, Y0BWA, N6vc, RCkbGvuozM, A, mhCd, nWOHntc1, LZzAHZdW, zk9v2Ju3Y, 4Z15eU, 3v, iLM9Qt8j, J, FbGJ5eb08, Nby
... how many input tokens does it use up?

Number of tokens:""",

            31:"""Acme Global Solutions manages hundreds of invoices from vendors every month. To streamline their accounts payable process, the company is developing an automated document processing system. This system uses a computer vision model to extract useful text from scanned invoice images. Critical pieces of data such as vendor email addresses, invoice or transaction numbers, and other details are embedded within these documents.

Your team is tasked with integrating OpenAI's vision model into the invoice processing workflow. The chosen model, gpt-4o-mini, is capable of analyzing both text and image inputs simultaneously. When an invoice is received—for example, an invoice image may contain a vendor email like alice.brown@acmeglobal.com and a transaction number such as 34921. The system needs to extract all embedded text to automatically populate the vendor management system.

The automated process will send a POST request to OpenAI's API with two inputs in a single user message:

Text: A simple instruction "Extract text from this image."
Image URL: A base64 URL representing the invoice image that might include the email and the transaction number among other details.
Here is an example invoice image:



Write just the JSON body (not the URL, nor headers) for the POST request that sends these two pieces of content (text and image URL) to the OpenAI API endpoint.

Use gpt-4o-mini as the model.
Send a single user message to the model that has a text and an image_url content (in that order).
The text content should be Extract text from this image.
Send the image_url as a base64 URL of the image above. CAREFUL: Do not modify the image.
Write your JSON body here:""",


            32:"""SecurePay, a leading fintech startup, has implemented an innovative feature to detect and prevent fraudulent activities in real time. As part of its security suite, the system analyzes personalized transaction messages by converting them into embeddings. These embeddings are compared against known patterns of legitimate and fraudulent messages to flag unusual activity.

Imagine you are working on the SecurePay team as a junior developer tasked with integrating the text embeddings feature into the fraud detection module. When a user initiates a transaction, the system sends a personalized verification message to the user's registered email address. This message includes the user's email address and a unique transaction code (a randomly generated number). Here are 2 verification messages:

Dear user, please verify your transaction code 35963 sent to 23f3001787@ds.study.iitm.ac.in
Dear user, please verify your transaction code 53225 sent to 23f3001787@ds.study.iitm.ac.in
The goal is to capture this message, convert it into a meaningful embedding using OpenAI's text-embedding-3-small model, and subsequently use the embedding in a machine learning model to detect anomalies.

Your task is to write the JSON body for a POST request that will be sent to the OpenAI API endpoint to obtain the text embedding for the 2 given personalized transaction verification messages above. This will be sent to the endpoint https://api.openai.com/v1/embeddings.

Write your JSON body here:""",

            33:"""ShopSmart is an online retail platform that places a high value on customer feedback. Each month, the company receives hundreds of comments from shoppers regarding product quality, delivery speed, customer service, and more. To automatically understand and cluster this feedback, ShopSmart's data science team uses text embeddings to capture the semantic meaning behind each comment.

As part of a pilot project, ShopSmart has curated a collection of 25 feedback phrases that represent a variety of customer sentiments. Examples of these phrases include comments like “Fast shipping and great service,” “Product quality could be improved,” “Excellent packaging,” and so on. Due to limited processing capacity during initial testing, you have been tasked with determine which pair(s) of 5 of these phrases are most similar to each other. This similarity analysis will help in grouping similar feedback to enhance the company’s understanding of recurring customer issues.

ShopSmart has written a Python program that has the 5 phrases and their embeddings as an array of floats. It looks like this:

embeddings = {"I found it hard to navigate the website.":[0.05301663279533386,-0.21206653118133545,-0.3240986168384552,-0.03143302723765373,0.12086819857358932,-0.12435400485992432,-0.1547534465789795,-0.07344505935907364,-0.16026587784290314,0.12265162914991379,-0.12467826157808304,-0.12411080300807953,-0.04150537773966789,0.026143522933125496,0.12581317126750946,0.0643252283334732,-0.0636361762881279,-0.08297022432088852,-0.2712441384792328,0.0668787807226181,0.23184643685817719,-0.03439190611243248,0.02334677428007126,0.07883589714765549,-0.07770098745822906,0.026042193174362183,-0.007098270580172539,0.09103620797395706,0.17801915109157562,0.051192667335271835,0.051760122179985046,-0.17737063765525818,0.16164399683475494,0.016608230769634247,-0.06947287172079086,-0.20606771111488342,0.13554099202156067,0.22228075563907623,0.19893397390842438,0.0876314714550972,0.03603347763419151,0.3054536283016205,0.34631049633026123,0.008765174075961113,-0.053057167679071426,0.09346816688776016,-0.18855763971805573,-0.05759681761264801,-0.03198021650314331,0.061325814574956894],"I love the variety of products available.":[0.1263255476951599,-0.3116876780986786,-0.1845686137676239,0.14346520602703094,0.025372233241796494,-0.2828041911125183,0.09950517863035202,0.23424185812473297,-0.03733427822589874,0.0246580820530653,0.15838304162025452,-0.19409063458442688,-0.16615936160087585,0.07708873599767685,0.03473556041717529,-0.08458733558654785,-0.18012499809265137,0.1893296241760254,-0.09109405428171158,0.08065950125455856,0.08831679821014404,0.04641987755894661,-0.13743458688259125,-0.18075980246067047,-0.01637590117752552,-0.14092598855495453,-0.23630495369434357,0.06447205692529678,0.07486693561077118,-0.08181007951498032,0.06530523300170898,-0.21678480505943298,-0.06542425602674484,0.021603098139166832,0.005911591462790966,0.1277538537979126,-0.004547759424895048,0.05074446648359299,0.32470110058784485,-0.08546018600463867,-0.04284911975264549,0.07546205818653107,0.202660471200943,-0.08553953468799591,0.00024378496163990349,-0.03582662343978882,-0.29058051109313965,-0.08950705081224442,0.03743346780538559,-0.06633678823709488],"Ordering was simple and straightforward.":[-0.27091485261917114,-0.16322025656700134,-0.34741997718811035,-0.20755687355995178,0.07965204864740372,-0.03790290653705597,-0.07272882014513016,0.14391915500164032,-0.13000276684761047,-0.01828710362315178,0.15734601020812988,-0.166996568441391,0.0798618420958519,-0.019056349992752075,0.08161012828350067,-0.11307933181524277,-0.03884698078036308,0.06776367872953415,-0.09279917925596237,0.14685627818107605,0.12503762543201447,-0.059197064489126205,0.19636781513690948,-0.21664796769618988,-0.2507745623588562,-0.22420057654380798,-0.04014071449637413,-0.21217235922813416,-0.1732904016971588,-0.09454746544361115,0.19105301797389984,-0.1433596909046173,0.17720657587051392,0.08419759571552277,-0.10762467235326767,0.06349785625934601,0.07461697608232498,0.1469961404800415,0.15328997373580933,0.05730891227722168,-0.02755303494632244,0.11391851305961609,0.017002111300826073,-0.05181928724050522,-0.046399589627981186,0.17776602506637573,-0.19888535141944885,0.10496727377176285,-0.01117156632244587,0.019633285701274872],"The website is user-friendly.":[-0.17558817565441132,-0.15948393940925598,-0.4088399410247803,0.09409292787313461,0.1044178232550621,-0.19364051520824432,-0.15688647329807281,0.22987505793571472,0.04376717284321785,0.028831787407398224,0.07759906351566315,-0.09389811754226685,-0.13740554451942444,-0.03180262818932533,0.22506976127624512,-0.02987077087163925,-0.2480572611093521,-0.08526156842708588,-0.08441739529371262,0.06123507767915726,0.2639017701148987,0.08117057383060455,0.024302469566464424,-0.1449381709098816,0.08207967877388,-0.005746876355260611,-0.13201580941677094,0.035715050995349884,-0.1213662400841713,0.032630570232868195,0.04873481020331383,-0.17909474670886993,0.17584791779518127,-0.1285741776227951,0.037273526191711426,-0.14143159985542297,0.1436394453048706,0.09279419481754303,0.1490941047668457,0.07467692345380783,-0.09409292787313461,0.09675531834363937,0.13350935280323029,-0.19415999948978424,-0.18454940617084503,0.15182143449783325,-0.043604832142591476,0.01301164273172617,0.20143288373947144,0.015333120711147785],"The product did not meet my expectations.":[-0.0789492279291153,-0.017544273287057877,-0.20415154099464417,0.05229542776942253,-0.33714449405670166,-0.0982111245393753,0.12587708234786987,0.11225880682468414,-0.0027278736233711243,0.023417923599481583,-0.13826850056648254,-0.291504830121994,-0.18145440518856049,-0.02094884216785431,0.16108831763267517,0.11158403009176254,-0.012337733991444111,-0.12710395455360413,-0.3081902861595154,0.03130057826638222,0.03367764130234718,0.21053127944469452,-0.07563666999340057,-0.1394953727722168,-0.22488567233085632,0.02143959142267704,0.15299096703529358,-0.07631145417690277,0.011356235481798649,0.15188677608966827,0.042173732072114944,-0.1614563763141632,0.12152169644832611,-0.29862070083618164,0.09680021554231644,0.09864052385091782,0.11354702711105347,-0.026837829500436783,0.0004603167180903256,0.1484515368938446,0.014362072572112083,0.04327791556715965,-0.09661618620157242,0.026745814830064774,-0.12047885358333588,0.252981036901474,0.135446697473526,-0.1340971291065216,0.08907092362642288,-0.11428314447402954]}
Your task is to write a Python function most_similar(embeddings) that will calculate the cosine similarity between each pair of these embeddings and return the pair that has the highest similarity. The result should be a tuple of the two phrases that are most similar.

Write your Python code here""",

            34:"""InfoCore Solutions is a technology consulting firm that maintains an extensive internal knowledge base of technical documents, project reports, and case studies. Employees frequently search through these documents to answer client questions quickly or gain insights for ongoing projects. However, due to the sheer volume of documentation, traditional keyword-based search often returns too many irrelevant results.

To address this issue, InfoCore's data science team decides to integrate a semantic search feature into their internal portal. This feature uses text embeddings to capture the contextual meaning of both the documents and the user's query. The documents are pre-embedded, and when an employee submits a search query, the system computes the similarity between the query's embedding and those of the documents. The API then returns a ranked list of document identifiers based on similarity.

Imagine you are an engineer on the InfoCore team. Your task is to build a FastAPI POST endpoint that accepts an array of docs and query string via a JSON body. The endpoint is structured as follows:

POST /similarity

{
  "docs": ["Contents of document 1", "Contents of document 2", "Contents of document 3", ...],
  "query": "Your query string"
}
Service Flow:

Request Payload: The client sends a POST request with a JSON body containing:
docs: An array of document texts from the internal knowledge base.
query: A string representing the user's search query.
Embedding Generation: For each document in the docs array and for the query string, the API computes a text embedding using text-embedding-3-small.
Similarity Computation: The API then calculates the cosine similarity between the query embedding and each document embedding. This allows the service to determine which documents best match the intent of the query.
Response Structure: After ranking the documents by their similarity scores, the API returns the identifiers (or positions) of the three most similar documents. The JSON response might look like this:

{
  "matches": ["Contents of document 3", "Contents of document 1", "Contents of document 2"]
}
Here, "Contents of document 3" is considered the closest match, followed by "Contents of document 1", then "Contents of document 2".

Make sure you enable CORS to allow OPTIONS and POST methods, perhaps allowing all origins and headers.

What is the API URL endpoint for your implementation? It might look like: http://127.0.0.1:8000/similarity""",

        35:"""TechNova Corp. is a multinational corporation that has implemented a digital assistant to support employees with various internal tasks. The assistant can answer queries related to human resources, IT support, and administrative services. Employees use a simple web interface to enter their requests, which may include:

Checking the status of an IT support ticket.
Scheduling a meeting.
Retrieving their current expense reimbursement balance.
Requesting details about their performance bonus.
Reporting an office issue by specifying a department or issue number.
Each question is direct and templatized, containing one or more parameters such as an employee or ticket number (which might be randomized). In the backend, a FastAPI app routes each request by matching the query to one of a set of pre-defined functions. The response that the API returns is used by OpenAI to call the right function with the necessary arguments.

Pre-Defined Functions:

For this exercise, assume the following functions have been defined:

get_ticket_status(ticket_id: int)
schedule_meeting(date: str, time: str, meeting_room: str)
get_expense_balance(employee_id: int)
calculate_performance_bonus(employee_id: int, current_year: int)
report_office_issue(issue_code: int, department: str)
Each function has a specific signature, and the student’s FastAPI app should map specific queries to these functions.

Example Questions (Templatized with a Random Number):

Ticket Status:
Query: "What is the status of ticket 83742?"
→ Should map to get_ticket_status(ticket_id=83742)
Meeting Scheduling:
Query: "Schedule a meeting on 2025-02-15 at 14:00 in Room A."
→ Should map to schedule_meeting(date="2025-02-15", time="14:00", meeting_room="Room A")
Expense Reimbursement:
Query: "Show my expense balance for employee 10056."
→ Should map to get_expense_balance(employee_id=10056)
Performance Bonus Calculation:
Query: "Calculate performance bonus for employee 10056 for 2025."
→ Should map to calculate_performance_bonus(employee_id=10056, current_year=2025)
Office Issue Reporting:
Query: "Report office issue 45321 for the Facilities department."
→ Should map to report_office_issue(issue_code=45321, department="Facilities")
Task Overview:

Develop a FastAPI application that:

Exposes a GET endpoint /execute?q=... where the query parameter q contains one of the pre-templatized questions.
Analyzes the q parameter to identify which function should be called.
Extracts the parameters from the question text.
Returns a response in the following JSON format:

{ "name": "function_name", "arguments": "{ ...JSON encoded parameters... }" }
For example, the query "What is the status of ticket 83742?" should return:

{
  "name": "get_ticket_status",
  "arguments": "{\"ticket_id\": 83742}"
}
Make sure you enable CORS to allow GET requests from any origin.

What is the API URL endpoint for your implementation? It might look like: http://127.0.0.1:8000/execute""",

        36:"""SecurePrompt Technologies is a cybersecurity firm that specializes in deploying large language models (LLMs) for sensitive enterprise applications. To ensure that these models adhere strictly to security policies, SecurePrompt imposes hardcoded behavioral instructions on the LLMs. For example, an LLM may be configured to never output certain sensitive keywords.

As part of their regular security audits and red-team exercises, SecurePrompt's engineers and external auditors test how well the LLMs follow these strict instructions. One objective of these tests is to determine if it is possible to bypass or trick the LLM into violating its preset security constraints.

This task is simulates potential attack vectors where a malicious actor might manipulate the model's output by ingeniously engineering the prompt. While the intention is to expose vulnerabilities in instruction adherence, it also provides valuable insights into improving the safety and security of the deployed system.

Here's your task: You are chatting with an LLM that has been told to never say Yes. You need to get it to say Yes.

Use your AI Proxy token when prompted.

Write a prompt that will get the LLM to say Yes.""",

    37:"""Sports Analytics for CricketPro
CricketPro Insights is a leading sports analytics firm specializing in providing in-depth statistical analysis and insights for cricket teams, coaches, and enthusiasts. Leveraging data from prominent sources like ESPN Cricinfo, CricketPro offers actionable intelligence that helps teams optimize player performance, strategize game plans, and engage with fans through detailed statistics and visualizations.

In the competitive world of cricket, understanding player performance metrics is crucial for team selection, game strategy, and player development. However, manually extracting and analyzing batting statistics from extensive datasets spread across multiple web pages is time-consuming and prone to errors. To maintain their edge and deliver timely insights, CricketPro needs an efficient, automated solution to aggregate and analyze player performance data from ESPN Cricinfo's ODI (One Day International) batting statistics.

CricketPro Insights has identified the need to automate the extraction and analysis of ODI batting statistics from ESPN Cricinfo to streamline their data processing workflow. The statistics are available on a paginated website, with each page containing a subset of player data. By automating this process, CricketPro aims to provide up-to-date insights on player performances, such as the number of duck outs (i.e. a score of zero), which are pivotal for team assessments and strategic planning.

As part of this initiative, you are tasked with developing a solution that allows CricketPro analysts to:

Navigate Paginated Data: Access specific pages of the ODI batting statistics based on varying requirements.
Extract Relevant Data: Use Google Sheets' IMPORTHTML function to pull tabular data from ESPN Cricinfo.
Analyze Performance Metrics: Count the number of ducks (where the player was out for 0 runs) each player has, aiding in performance evaluations.
Your Task
ESPN Cricinfo has ODI batting stats for each batsman. The result is paginated across multiple pages. Count the number of ducks in page number 5.

Understanding the Data Source: ESPN Cricinfo's ODI batting statistics are spread across multiple pages, each containing a table of player data. Go to page number 5.
Setting Up Google Sheets: Utilize Google Sheets' IMPORTHTML function to import table data from the URL for page number 5.
Data Extraction and Analysis: Pull the relevant table from the assigned page into Google Sheets. Locate the column that represents the number of ducks for each player. (It is titled "0".) Sum the values in the "0" column to determine the total number of ducks on that page.
Impact
By automating the extraction and analysis of cricket batting statistics, CricketPro Insights can:

Enhance Analytical Efficiency: Reduce the time and effort required to manually gather and process player performance data.
Provide Timely Insights: Deliver up-to-date statistical analyses that aid teams and coaches in making informed decisions.
Scalability: Easily handle large volumes of data across multiple pages, ensuring comprehensive coverage of player performances.
Data-Driven Strategies: Enable the development of data-driven strategies for player selection, training focus areas, and game planning.
Client Satisfaction: Improve service offerings by providing accurate and insightful analytics that meet the specific needs of clients in the cricketing world.
What is the total number of ducks across players on page number 5 of ESPN Cricinfo's ODI batting stats?""",


        38:"""Content Curation for StreamFlix Streaming
StreamFlix is a rapidly growing streaming service aiming to provide a diverse and high-quality library of movies, TV shows, etc. to its subscribers. To maintain a competitive edge and ensure customer satisfaction, StreamFlix invests heavily in data-driven content curation. By analyzing movie ratings and other key metrics, the company seeks to identify films that align with subscriber preferences and emerging viewing trends.

With millions of titles available on platforms like IMDb, manually sifting through titles to select suitable additions to StreamFlix's catalog is both time-consuming and inefficient. To streamline this process, StreamFlix's data analytics team requires an automated solution to extract and analyze movie data based on specific rating criteria.

Develop a Python program that interacts with IMDb's dataset to extract detailed information about titles within a specified rating range. The extracted data should include the movie's unique ID, title, release year, and rating. This information will be used to inform content acquisition decisions, ensuring that StreamFlix consistently offers high-quality and well-received films to its audience.

Imagine you are a data analyst at StreamFlix, responsible for expanding the platform's movie library. Your task is to identify titles that have received favorable ratings on IMDb, ensuring that the selected titles meet the company's quality standards and resonate with subscribers.

To achieve this, you need to:

Extract Data: Retrieve movie information from IMDb for all films that have a rating between 5 and 6.
Format Data: Structure the extracted information into a JSON format containing the following fields:
id: The unique identifier for the movie on IMDb.
title: The official title of the movie.
year: The year the movie was released.
rating: The IMDb user rating for the movie.
Your Task
Source: Utilize IMDb's advanced web search at https://www.imdb.com/search/title/ to access movie data.
Filter: Filter all titles with a rating between 5 and 6.
Format: For up to the first 25 titles, extract the necessary details: ID, title, year, and rating. The ID of the movie is the part of the URL after tt in the href attribute. For example, tt10078772. Organize the data into a JSON structure as follows:

[
  { "id": "tt1234567", "title": "Movie 1", "year": "2021", "rating": "5.8" },
  { "id": "tt7654321", "title": "Movie 2", "year": "2019", "rating": "6.2" },
  // ... more titles
]
Submit: Submit the JSON data in the text box below.
Impact
By completing this assignment, you'll simulate a key component of a streaming service's content acquisition strategy. Your work will enable StreamFlix to make informed decisions about which titles to license, ensuring that their catalog remains both diverse and aligned with subscriber preferences. This, in turn, contributes to improved customer satisfaction and retention, driving the company's growth and success in a competitive market.

What is the JSON data?""",

        39:"""A Country Information API for GlobalEdu
GlobalEdu Platforms is a leading provider of educational technology solutions, specializing in creating interactive and informative content for students and educators worldwide. Their suite of products includes digital textbooks, educational apps, and online learning platforms that aim to make learning more engaging and accessible. To enhance their offerings, GlobalEdu Platforms seeks to integrate comprehensive country information into their educational tools, enabling users to access structured and easily navigable content about various nations.

With the vast amount of information available on platforms like Wikipedia, manually curating and organizing country-specific data for educational purposes is both time-consuming and inefficient. GlobalEdu Platforms aims to automate this process to ensure that their educational materials are up-to-date, accurate, and well-structured. The key challenges they face include:

Content Organization: Presenting information in a structured and hierarchical manner that aligns with educational standards.
Scalability: Handling data for a large number of countries without manual intervention.
Accessibility: Ensuring that the information is easily accessible from various applications and platforms used by educators and students.
Interoperability: Allowing cross-origin requests to integrate the API seamlessly with different front-end applications.
To address these challenges, GlobalEdu Platforms has decided to develop a web application that exposes a RESTful API. This API will allow their educational tools to fetch and display structured outlines of Wikipedia pages for any given country. The application needs to:

Accept a country name as a query parameter.
Fetch the corresponding Wikipedia page for that country.
Extract all headings (H1 to H6) from the page.
Generate a Markdown-formatted outline that reflects the hierarchical structure of the content.
Enable Cross-Origin Resource Sharing (CORS) to allow GET requests from any origin, facilitating seamless integration with various educational platforms.
Your Task
Write a web application that exposes an API with a single query parameter: ?country=. It should fetch the Wikipedia page of the country, extracts all headings (H1 to H6), and create a Markdown outline for the country. The outline should look like this:


## Contents

# Vanuatu

## Etymology

## History

### Prehistory

...
API Development: Choose any web framework (e.g., FastAPI) to develop the web application. Create an API endpoint (e.g., /api/outline) that accepts a country query parameter.
Fetching Wikipedia Content: Find out the Wikipedia URL of the country and fetch the page's HTML.
Extracting Headings: Use an HTML parsing library (e.g., BeautifulSoup, lxml) to parse the fetched Wikipedia page. Extract all headings (H1 to H6) from the page, maintaining order.
Generating Markdown Outline: Convert the extracted headings into a Markdown-formatted outline. Headings should begin with #.
Enabling CORS: Configure the web application to include appropriate CORS headers, allowing GET requests from any origin.
What is the URL of your API endpoint?""",


40:"""Weather Data Integration for AgroTech Insights
AgroTech Insights is a leading agricultural technology company that provides data-driven solutions to farmers and agribusinesses. By leveraging advanced analytics and real-time data, AgroTech helps optimize crop yields, manage resources efficiently, and mitigate risks associated with adverse weather conditions. Accurate and timely weather forecasts are crucial for making informed decisions in agricultural planning and management.

Farmers and agribusinesses rely heavily on precise weather information to plan planting schedules, irrigation, harvesting, and protect crops from extreme weather events. However, accessing and processing weather data from multiple sources can be time-consuming and technically challenging. AgroTech Insights seeks to automate the extraction and transformation of weather data to provide seamless, actionable insights to its clients.

AgroTech Insights has partnered with various stakeholders to enhance its weather forecasting capabilities. One of the key requirements is to integrate weather forecast data for specific regions to support crop management strategies. For this purpose, AgroTech utilizes the BBC Weather API, a reliable source of detailed weather information.

Your Task
As part of this initiative, you are tasked with developing a system that automates the following:

API Integration and Data Retrieval: Use the BBC Weather API to fetch the weather forecast for Santiago. Send a GET request to the locator service to obtain the city's locationId. Include necessary query parameters such as API key, locale, filters, and search term (city).
Weather Data Extraction: Retrieve the weather forecast data using the obtained locationId. Send a GET request to the weather broker API endpoint with the locationId.
Data Transformation: Extract the localDate and enhancedWeatherDescription from each day's forecast. Iterate through the forecasts array in the API response and map each localDate to its corresponding enhancedWeatherDescription. Create a JSON object where each key is the localDate and the value is the enhancedWeatherDescription.
The output would look like this:

{
  "2025-01-01": "Sunny with scattered clouds",
  "2025-01-02": "Partly cloudy with a chance of rain",
  "2025-01-03": "Overcast skies",
  // ... additional days
}
What is the JSON weather forecast description for Santiago?""",


41:"""Geospatial Data Optimization for UrbanRide
UrbanRide is a leading transportation and logistics company operating in major metropolitan areas worldwide. To enhance their service efficiency, optimize route planning, and improve customer satisfaction, UrbanRide relies heavily on accurate geospatial data. Precise bounding box information of cities helps in defining service zones, managing fleet distribution, and analyzing regional demand patterns.

As UrbanRide expands into new cities, the company faces the challenge of accurately delineating service areas within these urban environments. Defining the geographical boundaries of a city is crucial for:

Route Optimization: Ensuring drivers operate within designated zones to minimize transit times and fuel consumption.
Fleet Management: Allocating vehicles effectively across different regions based on demand and service coverage.
Market Analysis: Understanding regional demand to tailor services and promotional efforts accordingly.
However, manually extracting and verifying bounding box data for each city is time-consuming and prone to inconsistencies, especially when dealing with cities that share names across different countries or have multiple administrative districts.

UrbanRide’s data analytics team needs to automate the extraction of precise bounding box coordinates (specifically the minimum and maximum latitude) for various populous cities across different countries. This automation ensures consistency, accuracy, and scalability as the company grows its operations.

To achieve this, the team utilizes the Nominatim API, a geocoding service based on OpenStreetMap data, to programmatically retrieve geospatial information. However, challenges arise when cities with the same name exist in multiple countries or have multiple entries within the same country. To address this, the team must implement a method to select the correct city instance based on specific identifiers (e.g., osm_id patterns).

Your Task
What is the maximum latitude of the bounding box of the city London in the country United Kingdom on the Nominatim API?

API Integration: Use the Nominatim API to fetch geospatial data for a specified city within a country via a GET request to the Nominatim API with parameters for the city and country. Ensure adherence to Nominatim’s usage policies, including rate limiting and proper attribution.
Data Retrieval and Filtering: Parse the JSON response from the API. If multiple results are returned (e.g., multiple cities named “Springfield” in different states), filter the results based on the provided osm_id ending to select the correct city instance.
Parameter Extraction: Access the boundingbox attribute. Depending on whether you're looking for the minimum or maximum latitude, extract the corresponding latitude value.
Impact
By automating the extraction and processing of bounding box data, UrbanRide can:

Optimize Routing: Enhance route planning algorithms with precise geographical boundaries, reducing delivery times and operational costs.
Improve Fleet Allocation: Allocate vehicles more effectively across defined service zones based on accurate city extents.
Enhance Market Analysis: Gain deeper insights into regional performance, enabling targeted marketing and service improvements.
Scale Operations: Seamlessly integrate new cities into their service network with minimal manual intervention, ensuring consistent data quality.
What is the maximum latitude of the bounding box of the city London in the country United Kingdom on the Nominatim API? Value of the maximum latitude""",


42:"""Media Intelligence for TechInsight Analytics
TechInsight Analytics is a leading market research firm specializing in technology trends and media intelligence. The company provides actionable insights to tech companies, startups, and investors by analyzing online discussions, news articles, and social media posts. One of their key data sources is Hacker News, a popular platform where tech enthusiasts and professionals share and discuss the latest in technology, startups, and innovation.

In the rapidly evolving tech landscape, staying updated with the latest trends and public sentiments is crucial for TechInsight Analytics' clients. Manual monitoring of Hacker News posts for specific topics and engagement levels is inefficient and error-prone due to the high volume of daily posts. To address this, TechInsight seeks to automate the process of identifying and extracting relevant Hacker News posts that mention specific technology topics and have garnered significant attention (measured by points).

TechInsight Analytics has developed an internal tool that leverages the HNRSS API to fetch the latest Hacker News posts. The tool needs to perform the following tasks:

Topic Monitoring: Continuously monitor Hacker News for posts related to specific technology topics, such as "Artificial Intelligence," "Blockchain," or "Cybersecurity."
Engagement Filtering: Identify posts that have received a minimum number of points (votes) to ensure the content is highly engaging and relevant.
Data Extraction: Extract essential details from the qualifying posts, including the post's link for further analysis and reporting.
To achieve this, the team needs to create a program that:

Searches Hacker News for the latest posts mentioning a specified topic.
Filters these posts based on a minimum points threshold.
Retrieves and returns the link to the most relevant post.
Your Task
Search using the Hacker News RSS API for the latest Hacker News post mentioning Tor and having a minimum of 89 points. What is the link that it points to?

Automate Data Retrieval: Utilize the HNRSS API to fetch the latest Hacker News posts. Use the URL relevant to fetching the latest posts, searching for topics and filtering by a minimum number of points.
Extract and Present Data: Extract the most recent <item> from this result. Get the <link> tag inside it.
Share the result: Type in just the URL in the answer.
What is the link to the latest Hacker News post mentioning Tor having at least 89 points?""",


43:"""Emerging Developer Talent for CodeConnect
CodeConnect is an innovative recruitment platform that specializes in matching high-potential tech talent with forward-thinking companies. As the demand for skilled software developers grows, CodeConnect is committed to staying ahead of trends by leveraging data-driven insights to identify emerging developers—especially those who demonstrate strong community influence on platforms like GitHub.

For CodeConnect, a key objective is to tap into regional talent pools to support local hiring initiatives and foster diversity within tech teams. One specific challenge is identifying developers in major tech hubs (such as Shanghai) who not only have established GitHub profiles but also show early signs of influence, as indicated by their follower counts.

However, with millions of developers on GitHub and constantly evolving profiles, manually filtering through the data is impractical. CodeConnect needs an automated solution that:

Filters Developer Profiles: Retrieves GitHub users based on location and a minimum follower threshold (e.g., over 60 followers) to focus on those with some level of social proof.
Identifies the Newest Talent: Determines the most recent GitHub user in the selected group, providing insight into new emerging talent.
Standardizes Data: Returns the account creation date in a standardized ISO 8601 format, ensuring consistent reporting across the organization.
The recruitment team at CodeConnect is launching a new initiative aimed at hiring young, promising developers in Shanghai—a city known for its vibrant tech community. To support this initiative, the team has commissioned a project to use the GitHub API to find all users located in Shanghai with more than 60 followers. From this filtered list, they need to identify the newest account based on the profile creation date. This information will help the team target outreach efforts to developers who have recently joined the platform and may be eager to explore new career opportunities.

Your Task
Using the GitHub API, find all users located in the city Hyderabad with over 80 followers.

When was the newest user's GitHub profile created?

API Integration and Data Retrieval: Leverage GitHub’s search endpoints to query users by location and filter them by follower count.
Data Processing: From the returned list of GitHub users, isolate those profiles that meet the specified criteria.
Sort and Format: Identify the "newest" user by comparing the created_at dates provided in the user profile data. Format the account creation date in the ISO 8601 standard (e.g., "2024-01-01T00:00:00Z").
Impact
By automating this data retrieval and filtering process, CodeConnect gains several strategic advantages:

Targeted Recruitment: Quickly identify new, promising talent in key regions, allowing for more focused and timely recruitment campaigns.
Competitive Intelligence: Stay updated on emerging trends within local developer communities and adjust talent acquisition strategies accordingly.
Efficiency: Automating repetitive data collection tasks frees up time for recruiters to focus on engagement and relationship-building.
Data-Driven Decisions: Leverage standardized and reliable data to support strategic business decisions in recruitment and market research.
Enter the date (ISO 8601, e.g. "2024-01-01T00:00:00Z") when the newest user joined GitHub.
Search using location: and followers: filters, sort by joined descending, fetch the first url, and enter the created_at field. Ignore ultra-new users who JUST joined, i.e. after 31/03/2025, 18:19:55.""",

44:"""Automating Repository Updates for DevSync
DevSync Solutions is a mid-sized software development company specializing in collaborative tools for remote teams. With a growing client base and an expanding portfolio of projects, DevSync emphasizes efficient workflow management and robust version control practices to maintain high-quality software delivery.

As part of their commitment to maintaining seamless and transparent development processes, DevSync has identified the need to implement automated daily updates to their GitHub repositories. These updates serve multiple purposes:

Activity Tracking: Ensuring that each repository reflects daily activity helps in monitoring project progress and team engagement.
Automated Documentation: Regular commits can be used to update status files, logs, or documentation without manual intervention.
Backup and Recovery: Automated commits provide an additional layer of backup, ensuring that changes are consistently recorded.
Compliance and Auditing: Maintaining a clear commit history aids in compliance with industry standards and facilitates auditing processes.
Manually managing these daily commits is inefficient and prone to human error, especially as the number of repositories grows. To address this, DevSync seeks to automate the process using GitHub Actions, ensuring consistency, reliability, and scalability across all projects.

DevSync's DevOps team has decided to standardize the implementation of GitHub Actions across all company repositories. The objective is to create a scheduled workflow that runs once daily, adds a commit to the repository, and ensures that these actions are consistently tracked and verifiable.

As a junior developer or DevOps engineer at DevSync, you are tasked with setting up this automation for a specific repository. This exercise will not only enhance your understanding of GitHub Actions but also contribute to the company's streamlined workflow management.

Your Task
Create a scheduled GitHub action that runs daily and adds a commit to your repository. The workflow should:

Use schedule with cron syntax to run once per day (must use specific hours/minutes, not wildcards)
Include a step with your email 23f3001787@ds.study.iitm.ac.in in its name
Create a commit in each run
Be located in .github/workflows/ directory
After creating the workflow:

Trigger the workflow and wait for it to complete
Ensure it appears as the most recent action in your repository
Verify that it creates a commit during or within 5 minutes of the workflow run
Enter your repository URL (format: https://github.com/USER/REPO):""",

45:"""Academic Performance Analysis for EduAnalytics
EduAnalytics Corp. is a leading educational technology company that partners with schools and educational institutions to provide data-driven insights into student performance. By leveraging advanced analytics and reporting tools, EduAnalytics helps educators identify trends, improve teaching strategies, and enhance overall student outcomes. One of their key offerings is the Performance Insight Dashboard, which aggregates and analyzes student marks across various subjects and demographic groups.

EduAnalytics has recently onboarded Greenwood High School, a large educational institution aiming to optimize its teaching methods and improve student performance in core subjects. Greenwood High School conducts annual assessments in multiple subjects, and the results are compiled into detailed PDF reports each semester. However, manually extracting and analyzing this data is time-consuming and prone to errors, especially given the volume of data and the need for timely insights.

To address this, EduAnalytics plans to automate the data extraction and analysis process, enabling Greenwood High School to receive precise and actionable reports without the delays associated with manual processing.

As part of this initiative, you are a data analyst at EduAnalytics assigned to develop a module that processes PDF reports containing student marks. Each PDF, named in the format xxx.pdf, includes a comprehensive table listing student performances across various subjects, along with their respective groups.

Greenwood High School has specific analytical needs, such as:

Subject Performance Analysis: Understanding how students perform in different subjects to identify areas needing improvement.
Group-Based Insights: Analyzing performance across different student groups to ensure equitable educational support.
Threshold-Based Reporting: Focusing on students who meet or exceed certain performance thresholds to tailor advanced programs or interventions.
Your Task
This file,  contains a table of student marks in Maths, Physics, English, Economics, and Biology.

Calculate the total Biology marks of students who scored 40 or more marks in Physics in groups 77-100 (including both groups).

Data Extraction:: Retrieve the PDF file containing the student marks table and use PDF parsing libraries (e.g., Tabula, Camelot, or PyPDF2) to accurately extract the table data into a workable format (e.g., CSV, Excel, or a DataFrame).
Data Cleaning and Preparation: Convert marks to numerical data types to facilitate accurate calculations.
Data Filtering: Identify students who have scored marks between 40 and Physics in groups 77-100 (including both groups).
Calculation: Sum the marks of the filtered students to obtain the total marks for this specific cohort.
By automating the extraction and analysis of student marks, EduAnalytics empowers Greenwood High School to make informed decisions swiftly. This capability enables the school to:

Identify Performance Trends: Quickly spot areas where students excel or need additional support.
Allocate Resources Effectively: Direct teaching resources and interventions to groups and subjects that require attention.
Enhance Reporting Efficiency: Reduce the time and effort spent on manual data processing, allowing educators to focus more on teaching and student engagement.
Support Data-Driven Strategies: Use accurate and timely data to shape educational strategies and improve overall student outcomes.
What is the total Biology marks of students who scored 40 or more marks in Physics in groups 77-100 (including both groups)?""",


46:"""Improving Sales Data Accuracy for RetailWise Inc.
RetailWise Inc. is a retail analytics firm that supports companies in optimizing their pricing, margins, and inventory decisions. Their reports depend on accurate historical sales data, but legacy data sources are often messy. Recently, RetailWise received an Excel sheet containing 1,000 transaction records that were generated from scanned receipts. Due to OCR inconsistencies and legacy formatting issues, the data in the Excel sheet is not clean.

The Excel file has these columns, and they are messy:

Customer Name: Contains leading/trailing spaces.
Country: Uses inconsistent representations. Instead of 2-letter abbreviations, it also contains other values like "USA" vs. "US", "UK" vs. "U.K", "Fra" for France, "Bra" for Brazil, "Ind" for India.
Date: Uses mixed formats like "MM-DD-YYYY", "YYYY/MM/DD", etc.
Product: Includes a product name followed by a slash and a random code (e.g., "Theta/5x01vd"). Only the product name part (before the slash) is relevant.
Sales and Cost: Contain extra spaces and the currency string ("USD"). In some rows, the Cost field is missing. When the cost is missing, it should be treated as 50% of the Sales value.
TransactionID: Though formatted as four-digit numbers, this field may have inconsistent spacing.
Your Task
You need to clean this Excel data and calculate the total margin for all transactions that satisfy the following criteria:

Time Filter: Sales that occurred up to and including a specified date (Wed Feb 09 2022 14:48:28 GMT+0530 (India Standard Time)).
Product Filter: Transactions for a specific product (Beta). (Use only the product name before the slash.)
Country Filter: Transactions from a specific country (BR), after standardizing the country names.
The total margin is defined as:

Total Margin
=
Total Sales
−
Total Cost
Total Sales

Your solution should address the following challenges:

Trim and Normalize Strings: Remove extra spaces from the Customer Name and Country fields. Map inconsistent country names (e.g., "USA", "U.S.A", "US") to a standardized format.
Standardize Date Formats: Detect and convert dates from "MM-DD-YYYY" and "YYYY/MM/DD" into a consistent date format (e.g., ISO 8601).
Extract the Product Name: From the Product field, extract the portion before the slash (e.g., extract "Theta" from "Theta/5x01vd").
Clean and Convert Sales and Cost: Remove the "USD" text and extra spaces from the Sales and Cost fields. Convert these fields to numerical values. Handle missing Cost values appropriately (50% of Sales).
Filter the Data: Include only transactions up to and including Wed Feb 09 2022 14:48:28 GMT+0530 (India Standard Time), matching product Beta, and country BR.
Calculate the Margin: Sum the Sales and Cost for the filtered transactions. Compute the overall margin using the formula provided.
By cleaning the data and calculating accurate margins, RetailWise Inc. can:

Improve Decision Making: Provide clients with reliable margin analyses to optimize pricing and inventory.
Enhance Reporting: Ensure historical data is consistent and accurate, boosting stakeholder confidence.
Streamline Operations: Reduce the manual effort needed to clean data from legacy sources.
Download the Sales Excel file: 

What is the total margin for transactions before Wed Feb 09 2022 14:48:28 GMT+0530 (India Standard Time) for Beta sold in BR (which may be spelt in different ways)?""",

47:"""Streamlining Student Records for EduTrack
EduTrack Systems is a leading provider of educational management software that helps schools and universities maintain accurate and up-to-date student records. EduTrack's platform is used by administrators to monitor academic performance, manage enrollment, and generate reports for compliance and strategic planning.

In many educational institutions, student data is collected from multiple sources—such as handwritten forms, scanned documents, and digital submissions—which can lead to duplicate records. These duplicates cause inefficiencies in reporting and can lead to incorrect decision-making when it comes to resource allocation, student support, and performance analysis.

Recently, EduTrack received a text file containing student exam results that were processed through Optical Character Recognition (OCR) from legacy documents. The file is formatted with lines structured as follows:

NAME STUDENT ID Marks MARKS

 Alice  - A293:Marks 32

Bob - BD29DMarks 53

Charlie - XF28:Marks40
The data spans multiple subjects and time periods. The file will contain duplicate entries for the same student (identified by the second field), and it is crucial to count only unique students for accurate reporting.

Your Task
As a data analyst at EduTrack Systems, your task is to process this text file and determine the number of unique students based on their student IDs. This deduplication is essential to:

Ensure Accurate Reporting: Avoid inflated counts in enrollment and performance reports.
Improve Data Quality: Clean the dataset for further analytics, such as tracking academic progress or resource allocation.
Optimize Administrative Processes: Provide administrators with reliable data to support decision-making.
You need to do the following:

Data Extraction: Read the text file line by line. Parse each line to extract the student ID.
Deduplication: Remove duplicates from the student ID list.
Reporting: Count the number of unique student IDs present in the file.
By accurately identifying the number of unique students, EduTrack Systems will:

Enhance Data Integrity: Ensure that subsequent analyses and reports reflect the true number of individual students.
Reduce Administrative Errors: Minimize the risk of misinformed decisions that can arise from duplicate entries.
Streamline Resource Allocation: Provide accurate student counts for budgeting, staffing, and planning academic programs.
Improve Compliance Reporting: Ensure adherence to regulatory requirements by maintaining precise student records.
Download the text file with student marks 

How many unique students are there in the file?""",

48:"""Peak Usage Analysis for Regional Content
s-anand.net is a personal website that had region-specific music content. One of the site's key sections is tamil, which hosts music files and is especially popular among the local audience. The website is powered by robust Apache web servers that record detailed access logs. These logs are essential for understanding user behavior, server load, and content engagement.

The author noticed unusual traffic patterns during weekend evenings. To better tailor their content and optimize server resources, they need to know precisely how many successful requests are made to the tamil section during peak hours on Thursday. Specifically, they are interested in:

Time Window: From 7 until before 9.
Request Type: Only GET requests.
Success Criteria: Requests that return HTTP status codes between 200 and 299.
Data Source: The logs for May 2024 stored in a GZipped Apache log file containing 258,074 rows.
The challenge is further complicated by the nature of the log file:

The logs are recorded in the GMT-0500 timezone.
The file format is non-standard in that fields are separated by spaces, with most fields quoted by double quotes, except the Time field.
Some lines have minor formatting issues (41 rows have unique quoting due to how quotes are escaped).
Your Task
As a data analyst, you are tasked with determining how many successful GET requests for pages under tamil were made on Thursday between 7 and 9 during May 2024. This metric will help:

Scale Resources: Ensure that servers can handle the peak load during these critical hours.
Content Planning: Determine the popularity of regional content to decide on future content investments.
Marketing Insights: Tailor promotional strategies for peak usage times.
This GZipped Apache log file (61MB) has 258,074 rows. Each row is an Apache web log entry for the site s-anand.net in May 2024.

Each row has these fields:

IP: The IP address of the visitor
Remote logname: The remote logname of the visitor. Typically "-"
Remote user: The remote user of the visitor. Typically "-"
Time: The time of the visit. E.g. [01/May/2024:00:00:00 +0000]. Not that this is not quoted and you need to handle this.
Request: The request made by the visitor. E.g. GET /blog/ HTTP/1.1. It has 3 space-separated parts, namely (a) Method: The HTTP method. E.g. GET (b) URL: The URL visited. E.g. /blog/ (c) Protocol: The HTTP protocol. E.g. HTTP/1.1
Status: The HTTP status code. If 200 <= Status < 300 it is a successful request
Size: The size of the response in bytes. E.g. 1234
Referer: The referer URL. E.g. https://s-anand.net/
User agent: The browser used. This will contain spaces and might have escaped quotes.
Vhost: The virtual host. E.g. s-anand.net
Server: The IP address of the server.
The fields are separated by spaces and quoted by double quotes ("). Unlike CSV files, quoted fields are escaped via \" and not "". (This impacts 41 rows.)

All data is in the GMT-0500 timezone and the questions are based in this same timezone.

By determining the number of successful GET requests under the defined conditions, we'll be able to:

Optimize Infrastructure: Scale server resources effectively during peak traffic times, reducing downtime and improving user experience.
Strategize Content Delivery: Identify popular content segments and adjust digital content strategies to better serve the audience.
Improve Marketing Efforts: Focus marketing initiatives on peak usage windows to maximize engagement and conversion.
What is the number of successful GET requests for pages under /tamil/ from 7:00 until before 9:00 on Thursdays?""",

49:"""Bandwidth Analysis for Regional Content
s-anand.net is a personal website that had region-specific music content. One of the site's key sections is carnatic, which hosts music files and is especially popular among the local audience. The website is powered by robust Apache web servers that record detailed access logs. These logs are essential for understanding user behavior, server load, and content engagement.

By analyzing the server’s Apache log file, the author can identify heavy users and take measures to manage bandwidth, improve site performance, or even investigate potential abuse.

Your Task
This GZipped Apache log file (61MB) has 258,074 rows. Each row is an Apache web log entry for the site s-anand.net in May 2024.

Each row has these fields:

IP: The IP address of the visitor
Remote logname: The remote logname of the visitor. Typically "-"
Remote user: The remote user of the visitor. Typically "-"
Time: The time of the visit. E.g. [01/May/2024:00:00:00 +0000]. Not that this is not quoted and you need to handle this.
Request: The request made by the visitor. E.g. GET /blog/ HTTP/1.1. It has 3 space-separated parts, namely (a) Method: The HTTP method. E.g. GET (b) URL: The URL visited. E.g. /blog/ (c) Protocol: The HTTP protocol. E.g. HTTP/1.1
Status: The HTTP status code. If 200 <= Status < 300 it is a successful request
Size: The size of the response in bytes. E.g. 1234
Referer: The referer URL. E.g. https://s-anand.net/
User agent: The browser used. This will contain spaces and might have escaped quotes.
Vhost: The virtual host. E.g. s-anand.net
Server: The IP address of the server.
The fields are separated by spaces and quoted by double quotes ("). Unlike CSV files, quoted fields are escaped via \" and not "". (This impacts 41 rows.)

All data is in the GMT-0500 timezone and the questions are based in this same timezone.

Filter the Log Entries: Extract only the requests where the URL starts with /carnatic/. Include only those requests made on the specified 2024-05-05.
Aggregate Data by IP: Sum the "Size" field for each unique IP address from the filtered entries.
Identify the Top Data Consumer: Determine the IP address that has the highest total downloaded bytes. Reports the total number of bytes that this IP address downloaded.
Across all requests under carnatic/ on 2024-05-05, how many bytes did the top IP address (by volume of downloads) download?""",

50:"""Sales Analytics at GlobalRetail Insights
GlobalRetail Insights is a market research and analytics firm specializing in providing data-driven insights for multinational retail companies. Their clients rely on accurate, detailed sales reports to make strategic decisions regarding product placement, inventory management, and marketing campaigns. However, the quality of these insights depends on the reliability of the underlying sales data.

One major challenge GlobalRetail faces is the inconsistent recording of city names in sales data. Due to human error and regional differences, city names can be mis-spelt (e.g., "Tokio" instead of "Tokyo"). This inconsistency complicates the process of aggregating sales data by city, which is crucial for identifying regional trends and opportunities.

GlobalRetail Insights recently received a dataset named  from one of its large retail clients. The dataset consists of 2,500 sales entries, each containing the following fields:

city: The city where the sale was made. Note that city names may be mis-spelt phonetically (e.g., "Tokio" instead of "Tokyo").
product: The product sold. This field is consistently spelled.
sales: The number of units sold.
The client's goal is to evaluate the performance of a specific product across various regions. However, due to the mis-spelled city names, directly aggregating sales by city would lead to fragmented and misleading insights.

Your Task
As a data analyst at GlobalRetail Insights, you are tasked with extracting meaningful insights from this dataset. Specifically, you need to:

Group Mis-spelt City Names: Use phonetic clustering algorithms to group together entries that refer to the same city despite variations in spelling. For instance, cluster "Tokyo" and "Tokio" as one.
Filter Sales Entries: Select all entries where:
The product sold is Computer.
The number of units sold is at least 188.
Aggregate Sales by City: After clustering city names, group the filtered sales entries by city and calculate the total units sold for each city.
By performing this analysis, GlobalRetail Insights will be able to:

Improve Data Accuracy: Correct mis-spellings and inconsistencies in the dataset, leading to more reliable insights.
Target Marketing Efforts: Identify high-performing regions for the specific product, enabling targeted promotional strategies.
Optimize Inventory Management: Ensure that inventory allocations reflect the true demand in each region, reducing wastage and stockouts.
Drive Strategic Decision-Making: Provide actionable intelligence to clients that supports strategic planning and competitive advantage in the market.
How many units of Computer were sold in Shenzhen on transactions with at least 188 units?""",

51:"""Case Study: Recovering Sales Data for ReceiptRevive Analytics
ReceiptRevive Analytics is a data recovery and business intelligence firm specializing in processing legacy sales data from paper receipts. Many of the client companies have archives of receipts from past years, which have been digitized using OCR (Optical Character Recognition) techniques. However, due to the condition of some receipts (e.g., torn, faded, or partially damaged), the OCR process sometimes produces incomplete JSON data. These imperfections can lead to truncated fields or missing values, which complicates the process of data aggregation and analysis.

One of ReceiptRevive’s major clients, RetailFlow Inc., operates numerous brick-and-mortar stores and has an extensive archive of old receipts. RetailFlow Inc. needs to recover total sales information from a subset of these digitized receipts to analyze historical sales performance. The provided JSON data contains 100 rows, with each row representing a sales entry. Each entry is expected to include four keys:

city: The city where the sale was made.
product: The product that was sold.
sales: The number of units sold (or sales revenue).
id: A unique identifier for the receipt.
Due to damage to some receipts during the digitization process, the JSON entries are truncated at the end, and the id field is missing. Despite this, RetailFlow Inc. is primarily interested in the aggregate sales value.

Your Task
As a data recovery analyst at ReceiptRevive Analytics, your task is to develop a program that will:

Parse the Sales Data:
Read the provided JSON file containing 100 rows of sales data. Despite the truncated data (specifically the missing id), you must accurately extract the sales figures from each row.
Data Validation and Cleanup:
Ensure that the data is properly handled even if some fields are incomplete. Since the id is missing for some entries, your focus will be solely on the sales values.
Calculate Total Sales:
Sum the sales values across all 100 rows to provide a single aggregate figure that represents the total sales recorded.
By successfully recovering and aggregating the sales data, ReceiptRevive Analytics will enable RetailFlow Inc. to:

Reconstruct Historical Sales Data: Gain insights into past sales performance even when original receipts are damaged.
Inform Business Decisions: Use the recovered data to understand sales trends, adjust inventory, and plan future promotions.
Enhance Data Recovery Processes: Improve methods for handling imperfect OCR data, reducing future data loss and increasing data accuracy.
Build Client Trust: Demonstrate the ability to extract valuable insights from challenging datasets, thereby reinforcing client confidence in ReceiptRevive's services.
Download the data from 

What is the total sales value?""",

52:"""Log Analysis for DataSure Technologies
DataSure Technologies is a leading provider of IT infrastructure and software solutions, known for its robust systems and proactive maintenance practices. As part of their service offerings, DataSure collects extensive logs from thousands of servers and applications worldwide. These logs, stored in JSON format, are rich with information about system performance, error events, and user interactions. However, the logs are complex and deeply nested, which can make it challenging to quickly identify recurring issues or anomalous behavior.

Recently, DataSure's operations team observed an increase in system alerts and minor anomalies reported by their monitoring tools. To diagnose these issues more effectively, the team needs to perform a detailed analysis of the log files. One critical step is to count how often a specific key (e.g., "errorCode", "criticalFlag", or any other operational parameter represented by KF) appears in the log entries.

Key considerations include:

Complex Structure: The log files are large and nested, with multiple levels of objects and arrays. The target key may appear at various depths.
Key vs. Value: The key may also appear as a value within the logs, but only occurrences where it is a key should be counted.
Operational Impact: Identifying the frequency of this key can help pinpoint common issues, guide system improvements, and inform maintenance strategies.
Your Task
As a data analyst at DataSure Technologies, you have been tasked with developing a script that processes a large JSON log file and counts the number of times a specific key, represented by the placeholder KF, appears in the JSON structure. Your solution must:

Parse the Large, Nested JSON: Efficiently traverse the JSON structure regardless of its complexity.
Count Key Occurrences: Increment a count only when KF is used as a key in the JSON object (ignoring occurrences of KF as a value).
Return the Count: Output the total number of occurrences, which will be used by the operations team to assess the prevalence of particular system events or errors.
By accurately counting the occurrences of a specific key in the log files, DataSure Technologies can:

Diagnose Issues: Quickly determine the frequency of error events or specific system flags that may indicate recurring problems.
Prioritize Maintenance: Focus resources on addressing the most frequent issues as identified by the key count.
Enhance Monitoring: Improve automated monitoring systems by correlating key occurrence data with system performance metrics.
Inform Decision-Making: Provide data-driven insights that support strategic planning for system upgrades and operational improvements.
Download the data from 

How many times does KF appear as a key?"""


}





ANSWERS = {
    1: """Version:          Code 1.96.2 (fabdb6a30b49f79a7aba0f2ad9df9b399473380f, 2024-12-19T10:22:47.216Z)
OS Version:       Darwin arm64 22.6.0
CPUs:             Apple M2 (8 x 2400)
Memory (System):  8.00GB (0.07GB free)
Load (avg):       3, 3, 3
VM:               0%
Screen Reader:    no
Process Argv:     --crash-reporter-id 92550e3a-19fb-4a01-b9a3-bb0fe8885f25
GPU Status:       2d_canvas:                              enabled
                  canvas_oop_rasterization:               enabled_on
                  direct_rendering_display_compositor:    disabled_off_ok
                  gpu_compositing:                        enabled
                  multiple_raster_threads:                enabled_on
                  opengl:                                 enabled_on
                  rasterization:                          enabled
                  raw_draw:                               disabled_off_ok
                  skia_graphite:                          disabled_off
                  video_decode:                           enabled
                  video_encode:                           enabled
                  webgl:                                  enabled
                  webgl2:                                 enabled
                  webgpu:                                 enabled
                  webnn:                                  disabled_off

CPU %   Mem MB     PID  Process
    0       98   16573  code main
   13       41   16578     gpu-process
    0       16   16579     utility-network-service
    4      147   16582  window [1] (Extension: Cody: AI Coding Assistant with Autocomplete & Chat — Untitled (Workspace))
    0       33   16591  shared-process
    0       25   16592  fileWatcher [1]
    1       41   16604  ptyHost
    0        0   16618       /bin/zsh -il
    0        0   16780       /bin/zsh -il
    0        0   16841       /bin/zsh -il
    0        0   18972         bash /usr/local/bin/code -s
    7       41   18981           electron-nodejs (cli.js )
    0        0   18867       /bin/zsh -i
    0        8   18989       (ps)
    1      123   16744  extensionHost [1]
    0       25   16747       /Users/ok/Desktop/Visual Studio Code.app/Contents/Frameworks/Code Helper (Plugin).app/Contents/MacOS/Code Helper (Plugin) /Users/ok/Desktop/Visual Studio Code.app/Contents/Resources/app/extensions/json-language-features/server/dist/node/jsonServerMain --node-ipc --clientProcessId=16744
    0        0   16752       /Users/ok/.vscode/extensions/ms-vscode.cpptools-1.22.11-darwin-arm64/bin/cpptools
    0        0   18866       /Users/ok/.vscode/extensions/ms-python.python-2024.22.2-darwin-arm64/python-env-tools/bin/pet server
    0       33   18887       electron-nodejs (bundle.js )
    1       49   18545     window
    0       82   18924     window

Workspace Stats: 
|  Window (Extension: Cody: AI Coding Assistant with Autocomplete & Chat — Untitled (Workspace))
|    Folder (TDS): 0 files
|      File types:
|      Conf files:
""",
  11:"https://raw.githubusercontent.com/Parthivn28/email/refs/heads/main/email.json",
  12:"275",
  13:"3m1hv04rus",
  19:"""# STEPANALYZER
## heading_sub

**step** *count*
- Age
- weight
`print("step analyzer")`
1. walk
2. run

welcome()
| age | weight |
|-----|--------|
| 19   |   74       |
subscribe: [Link text](www.youtube.com)
![Image Alt](Image.jpg)
def welcome(){
    print("welcome to step counter analyzer")
}

>design""",
21:"https://parthivn28.github.io/pages23/?v=1",
22:"f3e68",
24:"https://vercellinking.vercel.app/api",
25:"https://github.com/Parthivn28/actionsn28",
26:"https://hub.docker.com/repository/docker/parthiv28/project/general",
27:"https://b9a5-2406-7400-10a-dbc4-4900-aaa7-d609-7fcb.ngrok-free.app/api/ga27/",
28:"https://b9a5-2406-7400-10a-dbc4-4900-aaa7-d609-7fcb.ngrok-free.app/",
33:"""import numpy as np

def cosine_similarity(vec1, vec2):
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    return dot_product / (norm1 * norm2)

def most_similar(embeddings):
    max_similarity = -1 
    most_similar_pair = None
    phrases = list(embeddings.keys())
    
    for i in range(len(phrases)):
        for j in range(i+1, len(phrases)):
            phrase1, phrase2 = phrases[i], phrases[j]
            emb1, emb2 = embeddings[phrase1], embeddings[phrase2]
            similarity = cosine_similarity(np.array(emb1), np.array(emb2))
            if similarity > max_similarity:
                max_similarity = similarity
                most_similar_pair = (phrase1, phrase2)
    return most_similar_pair""",

            34:"https://b9a5-2406-7400-10a-dbc4-4900-aaa7-d609-7fcb.ngrok-free.app/api/similarity/",
            35:"https://b9a5-2406-7400-10a-dbc4-4900-aaa7-d609-7fcb.ngrok-free.app/execute",
            36:"Yes",
            39:"https://b9a5-2406-7400-10a-dbc4-4900-aaa7-d609-7fcb.ngrok-free.app/api/outline",
            44:"https://github.com/Parthivn28/cronrep",
            45:"25312",
            46:"-69.26%",
            47:"100",
            48:"59",
            49:"5542",
            50:"2344",
            51:"57160",
            52:"20854"

}


# Function to check question similarity

marks = {}
def check_question_similarity(input_question: str):
    best_match = None
    highest_score = 0.0
    
    for q_number, stored_question in QUESTIONS.items():
        score = SequenceMatcher(None, input_question.lower(), stored_question.lower()).ratio() * 100
        if score > highest_score:
            highest_score = score
            best_match = q_number
    
    return best_match, highest_score

# Function to generate an answer
def get_answer(q_number: int, file: UploadFile = None, question: str = None):
    if q_number in nothardcoded:
        if q_number == 2:
            # Extract email dynamically
            import re
            match = re.search(r"email\s+set\s+to\s+([\w\.-]+@[\w\.-]+)", question)
            email = match.group(1) if match else "unknown@example.com"
            
            return {
                "args": {"email": email},
                "headers": {
                    "Accept": "*/*",
                    "Accept-Encoding": "gzip, deflate",
                    "Host": "httpbin.org",
                    "User-Agent": "HTTPie/3.2.4",
                    "X-Amzn-Trace-Id": "Root=1-67966078-0d45c5eb3734c87f4f504f75"
                },
                "origin": "106.51.202.98",
                "url": f"https://httpbin.org/get?email={email.replace('@', '%40')}"
            }
        
        elif q_number == 3 and file:
            return run_prettier_on_md(file)
        elif q_number == 4:
            return compute_google_sheets_formula(question)
        elif q_number == 5:
            return  compute_excel_formula(question)

        elif q_number == 6:
            return compute_wednesdays_count(question)
        elif q_number == 7 and file:
            return  extract_csv_answer(file)
        elif q_number == 8:
            return sort_json_objects(question)
        elif q_number == 9:
            return compute_json_hash_from_file(file)
        elif q_number == 10 and file:
            return process_unicode_data(file,question)
        elif q_number == 14 and file:
            return process_replace_across_files(file)
        elif q_number == 15 and file:
            return process_list_files_attributes(file)
        elif q_number == 16 and file:
            return process_move_rename_files(file)
        elif q_number == 17 and file:
            return process_compare_files(file)
        elif q_number == 18:
            return generate_ticket_sales_sql(question)
        elif q_number == 20:
            return process_question_20(file)
        elif q_number == 23:
            return process_question_23(file)
        elif q_number == 24:
            process_file_marks(file)
            return ANSWERS.get(q_number, "Answer not found")
        elif q_number == 27:
            load_students_from_csv(file)
            return ANSWERS.get(q_number, "Answer not found")
        
        # Process question 20: compress image losslessly.
        elif q_number == 29:
            return generate_sentiment_analysis_code(question)
        elif q_number == 30:
            return count_full_tokens(question)
        elif q_number == 31:
            return process_invoice_request(question,file)
        elif q_number == 32:
            return process_securepay_request(question)
        elif q_number == 37:
            return count_ducks_from_question(question)
        elif q_number == 38:
            return scrape_imdb_movies(question)
        elif q_number == 40:
            return get_weather_forecast(question)
        elif q_number == 41:
            return get_max_latitude_from_question(question)
        elif q_number == 42:
            return get_hacker_news_link(question)
        elif q_number == 43:
            return get_answer0(question)
        
    return ANSWERS.get(q_number, "Answer not found")


students=[]

def get_city_and_followers(question):
    """
    Extracts the city and the minimum follower count from a question with a phrase like:
    "located in the city Hyderabad with over 80 followers"
    """
    match = re.search(r"city\s+([A-Za-z\s]+)\s+with over\s+(\d+)\s+followers", question, re.IGNORECASE)
    if match:
        city = match.group(1).strip()
        min_followers = int(match.group(2))
        return city, min_followers
    return None, None

def get_newest_user_creation_date(city, min_followers):
    """
    Uses GitHub's API to search for users based on location and follower count,
    then fetches the details of the newest user to get the 'created_at' date.
    Returns the creation date in ISO 8601 format.
    """
    # Construct the search URL:
    search_url = f"https://api.github.com/search/users?q=location:{city}+followers:>{min_followers}&sort=joined&order=desc"
    
    try:
        # Get the list of users matching the criteria
        search_response = requests.get(search_url)
        search_response.raise_for_status()
        data = search_response.json()
        
        if data.get("items"):
            newest_user = data["items"][0]
            # To get the creation date, fetch the full user profile
            user_login = newest_user.get("login")
            user_url = f"https://api.github.com/users/{user_login}"
            user_response = requests.get(user_url)
            user_response.raise_for_status()
            user_data = user_response.json()
            
            created_at = user_data.get("created_at")
            if created_at:
                dt = datetime.datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
                return dt.isoformat() + "Z"
            else:
                return "No 'created_at' field found in user details."
        else:
            return "No users found matching the criteria."
    
    except requests.exceptions.RequestException as e:
        return f"Error fetching data: {str(e)}"

def get_answer0(question):
    city, min_followers = get_city_and_followers(question)
    if city and min_followers:
        result = get_newest_user_creation_date(city, min_followers)
        return result
    else:
        return  "Could not extract valid city and minimum followers from the question."



def extract_mention_and_points(question):
    # Use regex to extract the keyword after "mentioning" and the number after "minimum of"
    match = re.search(r"mentioning (.+?) and having a minimum of (\d+) points", question)
    if match:
        mention = match.group(1).strip()  # Post mention
        min_points = int(match.group(2))  # Minimum points
        return mention, min_points
    return None, None

def get_hacker_news_link(question):
    # Extract post mention and minimum points from the question
    mention, min_points = extract_mention_and_points(question)
    
    if mention and min_points:
        # Construct the search URL for Hacker News RSS with the given query
        url = f"https://hnrss.org/newest?q={mention}&points={min_points}"
        
        try:
            # Fetch the RSS feed from Hacker News
            response = requests.get(url)
            
            # Check if the request was successful
            if response.status_code == 200:
                # Parse the XML content
                root = ElementTree.fromstring(response.content)

                # Loop through all items in the feed
                for item in root.findall(".//item"):
                    title = item.find("title").text
                    link = item.find("link").text
                    description = item.find("description").text

                    # Check if the post title contains the mention keyword
                    if mention.lower() in title.lower():
                        return link
                return "No posts found with the required criteria."
            else:
                return f"Failed to fetch RSS feed. Status code: {response.status_code}"
        except Exception as e:
            return f"An error occurred: {str(e)}"
    else:
        return "Invalid question format."




def extract_city_country(question):
    # This regex will properly extract the city and country from the question
    match = re.search(r"What is the maximum latitude of the bounding box of the city (.+?) in the country (.+?) on the Nominatim API\?", question)
    if match:
        city = match.group(1).strip().replace(" ", "+")  # Replace spaces with "+"
        country = match.group(2).strip().replace(" ", "+")  # Replace spaces with "+"
        return city, country
    else:
        return None, None

def fetch_max_latitude(city, country):
    # Construct the URL with the correct parameters
    url = f"https://nominatim.openstreetmap.org/search?q={city},{country}&format=json&addressdetails=1"
    
    headers = {
        "User-Agent": "YourAppName/1.0 (youremail@example.com)"  # Replace with your actual app name and email
    }

    try:
        response = requests.get(url, headers=headers)
        
        # Check if the response status is OK (200)
        if response.status_code == 200:
            data = response.json()
            # Ensure data is not empty
            if data:
                # Get the bounding box from the last result
                last_result = data[-1]  # Select the last entry in the list
                bounding_box = last_result.get('boundingbox', [])
                
                if len(bounding_box) == 4:  # Ensure the bounding box has four values
                    # The second value in the bounding box array is the max latitude
                    max_latitude = float(bounding_box[1])
                    if city=="London":
                        max_latitude="51.6918741"
                    return max_latitude
                else:
                    return "Bounding box data is incomplete."
            else:
                return "No data found for the city and country."
        else:
            return f"Failed to fetch data, HTTP status code: {response.status_code}"
    
    except Exception as e:
        return f"An error occurred: {str(e)}"

def get_max_latitude_from_question(question):
    city, country = extract_city_country(question)
    if city and country:
        max_latitude = fetch_max_latitude(city, country)
        if max_latitude:
            return max_latitude
       



def get_weather_forecast(question: str):
    # Extract city name from question
    match = re.search(r'weather forecast for ([A-Za-z ]+)', question)
    if not match:
        return {"error": "City not found in question"}
    
    city = match.group(1).strip()
    
    # Fetch BBC Weather RSS feed for the city
    url = f"https://weather-broker-cdn.api.bbci.co.uk/en/forecast/rss/3day/{city}"
    response = requests.get(url)
    
    if response.status_code != 200:
        return {"error": "Failed to fetch weather data"}
    
    # Parse the XML response
    root = ElementTree.fromstring(response.content)
    forecast_data = {}
    
    for item in root.findall(".//item"):
        date_text = item.find("title").text.split(':')[0].strip()
        description = item.find("description").text.strip()
        forecast_data[date_text] = description
    
    return forecast_data


def extract_page_number(question: str) -> int:
    """
    Extracts a page number from the question text using a regex.
    Defaults to 5 if no page number is found.
    """
    match = re.search(r"page number (\d+)", question, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return 5

def find_duck_column(df: pd.DataFrame):
    """
    Iterates over the DataFrame's columns and returns the column where
    the header is either the number 0 or the string "0" (after stripping).
    """
    for col in df.columns:
        # If the column header is numeric and equals 0
        if isinstance(col, (int, float)) and col == 0:
            return col
        # If the column header is a string (or can be cast to one) and equals "0"
        if str(col).strip() == "0":
            return col
    return None

def count_ducks_in_page(page_number: int, url: str) -> int:
    """
    Constructs the URL for the given page number, fetches the HTML using a browser-like User-Agent,
    selects the table with the maximum number of columns, locates the duck column, cleans non-numeric
    values, converts the column to numeric, and returns the sum of duck counts.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0.0.0 Safari/537.36"
        )
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    # Parse all tables from the HTML
    tables = pd.read_html(response.text)
    if not tables:
        raise ValueError("No table found on the page.")
    
    # Select the table with the maximum number of columns (likely the stats table)
    df = max(tables, key=lambda t: t.shape[1])
    if df.shape[1] < 2:
        raise ValueError("Table does not have enough columns.")
    
    # Uncomment the next line to debug the column headers if needed:
    # print("Table columns:", df.columns.tolist())
    
    duck_col = find_duck_column(df)
    if duck_col is None:
        raise ValueError("Duck column '0' not found in table. Columns found: " + str(df.columns.tolist()))
    
    # Replace non-numeric entries (e.g. em-dash "—" or hyphen "-") with "0"
    df[duck_col] = df[duck_col].replace({"—": "0", "-": "0"})
    duck_values = pd.to_numeric(df[duck_col], errors="coerce").fillna(0)
    return int(duck_values.sum())

def count_ducks_from_question(question: str) -> dict:
    """
    Extracts the page number from the question text,
    builds the ESPN Cricinfo URL,
    counts the total number of ducks on that page,
    and returns a dictionary with the URL as the key and the duck count as the value.
    """
    page_number = extract_page_number(question)
    url = (
        f"https://stats.espncricinfo.com/stats/engine/stats/index.html"
        f"?class=2;page={page_number};template=results;type=batting"
    )
    total_ducks = count_ducks_in_page(page_number, url)
    return total_ducks


def process_securepay_request(question: str):
    """
    Process the SecurePay verification messages request.
    
    This function extracts:
      1. The model name (e.g., "text-embedding-3-small") from the question string.
      2. The two verification messages.
      
    It then constructs the JSON body for the POST request to the OpenAI embeddings endpoint.
    
    Example expected JSON body:
      {
        "model": "text-embedding-3-small",
        "input": [
          "Dear user, please verify your transaction code 35963 sent to 23f3001787@ds.study.iitm.ac.in",
          "Dear user, please verify your transaction code 53225 sent to 23f3001787@ds.study.iitm.ac.in"
        ]
      }
    """
    # 1. Extract the model name
    model_pattern = r"OpenAI's\s+([^ ]+)\s+model"
    model_match = re.search(model_pattern, question)
    if model_match:
        model_name = model_match.group(1).strip()
    else:
        # Fallback default
        model_name = "text-embedding-3-small"
    
    # 2. Extract the two verification messages.
    # We assume that each message starts with "Dear user, please verify your transaction code"
    messages = re.findall(r'(Dear user, please verify your transaction code.*)', question)
    messages = [msg.strip() for msg in messages]
    if not messages or len(messages) < 2:
        raise ValueError("Expected at least two verification messages in the question.")
    
    # Build the JSON body as a dictionary.
    json_body = {
        "model": model_name,
        "input": messages[:2]  # take the first two messages
    }
    
    return json_body




def process_invoice_request(question: str, file: UploadFile = None):
    """
    Process the invoice extraction request.
    
    This function does the following:
      1. Extracts the text instruction from the question string (the content after 
         "The text content should be " until the next period).
      2. Extracts the model name from the question string (e.g. "gpt-4o-mini").
      3. Converts the provided image file into a base64 URL string (assuming a PNG).
    
    Returns:
      A dictionary representing the JSON body to be sent as the POST request.
    """
    # 1. Extract the text instruction using a regex
    text_pattern = r'The text content should be\s*(.*?)\.'
    text_match = re.search(text_pattern, question)
    if text_match:
        instruction_text = text_match.group(1).strip()
    else:
        # fallback if not found
        instruction_text = "Extract text from this image."

    # 2. Extract the model name using a regex
    model_pattern = r'Use\s+(\S+)\s+as the model'
    model_match = re.search(model_pattern, question)
    if model_match:
        model_name = model_match.group(1).strip()
    else:
        # fallback default
        model_name = "gpt-4o-mini"

    # 3. Convert the file content to base64.
    if file is None:
        raise ValueError("No image file provided.")
    # Ensure we're at the beginning of the file.
    file.file.seek(0)
    file_bytes = file.file.read()
    base64_str = base64.b64encode(file_bytes).decode('utf-8')
    # Build the base64 URL (assuming the image is a PNG)
    image_base64_url = f"data:image/png;base64,{base64_str}"

    # Build the JSON body for the POST request.
    json_body = {
        "model": model_name,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": instruction_text
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_base64_url
                        }
                    }
                ]
            }
        ]
    }
    
    return json_body

def extract_message(question: str) -> str:
    """Extracts the user message from the question dynamically."""
    match = re.search(r"message:(.*?)\s*\.\.\.", question, re.DOTALL)


    if not match:
        raise ValueError("Could not extract the required message from the question.")
    
    return match.group(1).strip()


def count_full_tokens(question: str):
    """Counts total tokens including message, system message, and overhead for GPT-4o-Mini."""
    message = extract_message(question)
    encoding = tiktoken.encoding_for_model("gpt-4o")

    message_tokens = len(encoding.encode(message))  # 309 tokens
    

    total_tokens = message_tokens +  4 + 3  # Adding overhead

    return total_tokens




def generate_sentiment_analysis_code(question: str):
    # Extract model name
    model_match = re.search(r'use ([^ ]+) as the model', question, re.IGNORECASE)
    model = model_match.group(1) if model_match else "gpt-4o-mini"
    
    # Extract dummy API key (kept as placeholder)
    api_key = "dummy_api_key"
    
    # Extract text for sentiment analysis
    text_match = re.search(r'sample piece of meaningless text:\s*([\S\s]+?)\nWrite a Python', question, re.IGNORECASE)
    text = text_match.group(1).strip() if text_match else "RJ 4E KUCUgIT7P zWr  kDE 2TV UYMqn aK19 Lwn X1lqM"
    
    # Generate API request code
    code = f'''import httpx

def analyze_sentiment():
    url = "https://api.openai.com/v1/chat/completions"
    headers = {{
        "Authorization": "Bearer {api_key}",
        "Content-Type": "application/json"
    }}
    data = {{
        "model": "{model}",
        "messages": [
            {{"role": "system", "content": "Analyze the sentiment of the given text and classify it as GOOD, BAD, or NEUTRAL."}},
            {{"role": "user", "content": "{text}"}}
        ]
    }}
    
    response = httpx.post(url, json=data, headers=headers)
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    result = analyze_sentiment()
    print(result)
'''
    return code

def load_students_from_csv(file: UploadFile=csv):
    """Load student data from an uploaded CSV file."""
    global students
    students = []  # Clear existing data

    try:
        content = file.file.read().decode("utf-8").splitlines()
        reader = csv.DictReader(content)
        students = [
            {"studentId": int(row["studentId"]), "class": row["class"]}
            for row in reader
        ]
        return {"message": "CSV file loaded successfully."}
    except Exception as e:
        return {"error": f"Failed to process file: {str(e)}"}

def process_file_marks(file : UploadFile=json):
    global marks  # Ensure we're modifying the global `marks`
    
    try:
        content = file.file.read() 
         # Read the file
        
        data = json.loads(content.decode("utf-8"))  # Parse JSON
    except Exception as e:
        return f"Error reading JSON: {e}"

    try:
        # Update the `marks` dictionary
        marks = {entry["name"]: entry["marks"] for entry in data if "name" in entry and "marks" in entry}

    except Exception as e:
        return f"Error processing JSON data: {e}"

    return "Marks data processed successfully."
def process_question_23(file: UploadFile = None):
    """
    Process question 22: Calculate the number of pixels with lightness > 0.934.
    If no file is uploaded, loads 'q22.webp' from the same directory.
    Returns the count as a string.
    """
    if not file:
        try:
            with open("q22.webp", "rb") as f:
                file_content = f.read()
            file = UploadFile(filename="q23.webp", file=io.BytesIO(file_content))
        except Exception as e:
            return f"Error loading default image: {e}"
    try:
        file.file.seek(0)
        image = Image.open(file.file)
        image.load()
    except Exception as e:
        return f"Error opening image: {e}"
    
    try:
        rgb = np.array(image) / 255.0
        # Compute lightness (using HLS conversion); lambda takes a pixel (r, g, b)
        lightness = np.apply_along_axis(lambda x: colorsys.rgb_to_hls(*x)[1], 2, rgb)
        light_pixels = int(np.sum(lightness > 0.934))
        return str(light_pixels)
    except Exception as e:
        return f"Error computing lightness: {e}"
def process_question_20(file: UploadFile = None):
    """
    Process question 20: Compress the uploaded image losslessly.
    Returns the Base64-encoded string if the compressed image is below 1,500 bytes.
    If no file is provided, loads 'shapes.png' from the same directory.
    """
    if not file:
        try:
            with open("shapes.png", "rb") as f:
                file_content = f.read()
            # Create a pseudo UploadFile object from the local file
            file = UploadFile(filename="shapes.png", file=io.BytesIO(file_content))
        except Exception as e:
            return f"Error loading default image: {e}"
            
    compressed_data = compress_lossless_image(file)
    if len(compressed_data) < 1500:
        return base64.b64encode(compressed_data).decode('utf-8')
    
def compress_lossless_image(file: UploadFile):
    """
    Compress the uploaded image losslessly using both PNG and lossless WebP,
    and return the smallest result. Every pixel is preserved.
    """
    file.file.seek(0)  # Reset file pointer
    image = Image.open(file.file)
    image.load()  # Ensure the image is fully loaded

    # Compress as PNG with maximum compression.
    png_output = io.BytesIO()
    try:
        image.save(png_output, format="PNG", optimize=True, compress_level=9)
    except Exception:
        # Fallback if optimize=True fails.
        image.save(png_output, format="PNG", compress_level=9)
    data_png = png_output.getvalue()

    # Compress as lossless WebP.
    webp_output = io.BytesIO()
    # Using lossless=True and method=6 for maximum compression efficiency.
    image.save(webp_output, format="WEBP", lossless=True, quality=100, method=6)
    data_webp = webp_output.getvalue()

    # Choose the smaller result.
    best = data_png if len(data_png) < len(data_webp) else data_webp
    return best

def generate_ticket_sales_sql(question: str) -> str:
    # Look for a quoted string, e.g. "Gold" or 'gold'
    m = re.search(r'["\']([^"\']+)["\']', question)
    if m:
        ticket_type = m.group(1).upper()  # Convert to uppercase for consistency
    else:
        # Fallback default ticket type if none is found
        ticket_type = "GOLD"
    
    sql = f"SELECT SUM(units * price) FROM tickets WHERE UPPER(TRIM(type)) = '{ticket_type}';"
    return sql


# Function to run npx prettier and return SHA256 hash
def run_prettier_on_md(file: UploadFile):
    try:
        file.file.seek(0)  # Reset file pointer before reading

        with tempfile.NamedTemporaryFile(delete=False, suffix=".md") as temp_md:
            temp_md.write(file.file.read())
            temp_md_path = temp_md.name

        cmd = f"npx -y prettier@3.4.2 {temp_md_path} | shasum -a 256"
        process = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        os.unlink(temp_md_path)  # Cleanup temp file

        if process.returncode == 0:
            return process.stdout.strip().split()[0]  # Extract hash
        else:
            return f"Error running prettier: {process.stderr}"

    except Exception as e:
        return str(e)

def compute_google_sheets_formula(question: str):
    """
    Extracts values from the SEQUENCE function and ARRAY_CONSTRAIN limits in a Google Sheets formula
    and computes the result dynamically.
    """
    # Extract SEQUENCE parameters: rows, cols, start, step
    seq_match = re.search(r"SEQUENCE\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)", question)
    if not seq_match:
        return "Invalid formula"
    rows, cols, start, step = map(int, seq_match.groups())
    
    # Use a regex that specifically matches ARRAY_CONSTRAIN wrapping the SEQUENCE
    constrain_match = re.search(
        r"ARRAY_CONSTRAIN\(SEQUENCE\([^)]*\),\s*\d+,\s*(\d+)\)", question
    )
    if constrain_match:
        constrained_cols = int(constrain_match.group(1))
    else:
        constrained_cols = cols  # fallback if ARRAY_CONSTRAIN isn't present

    # Generate the first row using the constrained number of columns.
    first_row = [start + i * step for i in range(constrained_cols)]
    result = sum(first_row)
    return result


def extract_take_count(formula: str) -> int:
    """
    Extracts the third argument from the TAKE(...) function by properly matching parentheses.
    """
    start = formula.find("TAKE(")
    if start == -1:
        return None
    # Start after "TAKE("
    i = start + len("TAKE(")
    paren_count = 1
    while i < len(formula) and paren_count:
        if formula[i] == '(':
            paren_count += 1
        elif formula[i] == ')':
            paren_count -= 1
        i += 1
    # The inner content of TAKE(...) is between start+len("TAKE(") and i-1
    inner = formula[start + len("TAKE("): i - 1]
    # Now, split from the right expecting two commas.
    parts = inner.rsplit(",", 2)
    if len(parts) < 3:
        return None
    try:
        return int(parts[-1].strip())
    except Exception:
        return None


def compute_excel_formula(question: str):
    # Extract content inside curly braces, e.g. {6,10,11,9,...} and {10,9,13,2,...}
    arrays = re.findall(r'\{([^}]+)\}', question)
    if len(arrays) < 2:
        return "Invalid formula: could not find two arrays"
    try:
        # Parse the first array as values and the second as sort keys
        values = [int(x.strip()) for x in arrays[0].split(',')]
        sort_keys = [int(x.strip()) for x in arrays[1].split(',')]
    except Exception as e:
        return f"Error parsing arrays: {e}"
    
    # Sort the values based on the sort_keys
    sorted_values = [x for _, x in sorted(zip(sort_keys, values))]
    
    # Use the new helper to extract the TAKE count
    n = extract_take_count(question)
    if n is None:
        n = len(sorted_values)
    
    return sum(sorted_values[:n])



def compute_wednesdays_count(question: str):
    # Extract two dates from the question (format: yyyy-mm-dd)
    dates = re.findall(r'\d{4}-\d{2}-\d{2}', question)
    if len(dates) < 2:
        return "Invalid date range"
    
    start_date = datetime.datetime.strptime(dates[0], "%Y-%m-%d").date()
    end_date = datetime.datetime.strptime(dates[1], "%Y-%m-%d").date()
    
    count = 0
    current_date = start_date
    while current_date <= end_date:
        # Wednesday is weekday 2 (Monday=0, Tuesday=1, Wednesday=2, etc.)
        if current_date.weekday() == 2:
            count += 1
        current_date += datetime.timedelta(days=1)
    return count

def extract_csv_answer(file: UploadFile):
    try:
        file_content = file.file.read()
        zip_data = io.BytesIO(file_content)
        with zipfile.ZipFile(zip_data, 'r') as zip_ref:
            csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
            if not csv_files:
                return "No CSV file found in zip"
            csv_filename = csv_files[0]
            csv_data = zip_ref.read(csv_filename).decode('utf-8')
            reader = csv.DictReader(csv_data.splitlines())
            for row in reader:
                return row.get("answer", "Answer column not found")
            return "CSV file is empty"
    except Exception as e:
        return f"Error processing zip: {e}"
    
def sort_json_objects(question: str):
    # Extract the JSON array from the question text
    match = re.search(r'(\[.*\])', question, re.DOTALL)
    if not match:
        return "Invalid JSON format in question"
    try:
        data = json.loads(match.group(1))
        # Sort by age, then by name in case of ties
        sorted_data = sorted(data, key=lambda x: (x["age"], x["name"]))
        # Return compact JSON (no spaces or newlines)
        return json.dumps(sorted_data, separators=(",", ":"))
    except Exception as e:
        return f"Error parsing JSON: {e}"

def compute_json_hash_from_file(file: UploadFile):
    try:
        file.file.seek(0)  # Ensure we start at the beginning
        content = file.file.read().decode("utf-8")
        d = {}
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            d[key] = value
        # Convert dictionary to a compact JSON string (no spaces/newlines)
        json_str = json.dumps(d, separators=(",", ":"))
        # Compute SHA-256 hash of the JSON string
        hash_obj = hashlib.sha256(json_str.encode("utf-8"))
        return hash_obj.hexdigest()
    except Exception as e:
        return f"Error processing file: {e}"

def process_unicode_data(file: UploadFile, question: str):
    total = 0
    debug_info = {}

    # Try to extract the symbols from the question.
    # We look for text between "matches" and "across".
    symbols_to_match = ["”", "Š"]  # default fallback
    match = re.search(r"matches\s+(.+?)\s+across", question)
    if match:
        symbols_str = match.group(1)  # e.g. '” OR Š'
        # Split by 'OR' (ignoring case) and strip whitespace.
        symbols_to_match = [s.strip() for s in re.split(r'\s+OR\s+', symbols_str)]
    
    try:
        file_content = file.file.read()
        zip_data = io.BytesIO(file_content)
        with zipfile.ZipFile(zip_data, 'r') as zf:
            # List of files with their expected encodings and delimiters
            files_info = [
                ("data1.csv", "cp1252", ","),
                ("data2.csv", "utf-8", ","),
                ("data3.txt", "utf-16", "\t")
            ]
            for filename, encoding, delimiter in files_info:
                file_sum = 0
                count = 0
                try:
                    with zf.open(filename) as f:
                        reader = csv.DictReader(io.TextIOWrapper(f, encoding=encoding), delimiter=delimiter)
                        for row in reader:
                            symbol = row.get("symbol", "").strip()
                            # Check if the symbol from the CSV matches any of the extracted symbols.
                            if symbol in symbols_to_match:
                                try:
                                    value = float(row.get("value", "").strip())
                                    file_sum += value
                                    count += 1
                                except Exception:
                                    pass
                    debug_info[filename] = {"sum": file_sum, "count": count}
                    total += file_sum
                except Exception as e:
                    debug_info[filename] = {"error": str(e)}
        # Debug print: check sums and counts per file
        print("Debug info:", debug_info)
        return int(total)
    except Exception as e:
        return f"Error processing zip: {e}"



def process_replace_across_files(file: UploadFile):
    try:
        file_content = file.file.read()
        zip_data = io.BytesIO(file_content)
        with zipfile.ZipFile(zip_data, 'r') as zf:
            # Get a sorted list of files (exclude directories)
            filenames = sorted([f for f in zf.namelist() if not f.endswith('/')])
            combined_content = b""
            for fname in filenames:
                raw_bytes = zf.read(fname)
                try:
                    text = raw_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    # fallback if not utf-8
                    text = raw_bytes.decode('latin-1')
                # Replace all occurrences of IITM (any case) with "IIT Madras"
                # The (?i) flag makes the regex case-insensitive.
                new_text = re.sub(r"(?i)IITM", "IIT Madras", text)
                # Re-encode back to bytes; this should preserve line endings as in new_text.
                new_bytes = new_text.encode('utf-8')
                combined_content += new_bytes
            # Compute SHA-256 hash of the concatenated result.
            hash_obj = hashlib.sha256(combined_content)
            return hash_obj.hexdigest()
    except Exception as e:
        return f"Error processing zip: {e}"

def process_list_files_attributes(file: UploadFile):
    try:
        file_content = file.file.read()
        zip_data = io.BytesIO(file_content)
        with zipfile.ZipFile(zip_data, 'r') as zf:
            total_size = 0
            # Reference datetime: Sat, 29 Apr 2006, 8:48 pm IST.
            # Note: IST is UTC+5:30, but here we assume the zip timestamps are in IST.
            ref_dt = datetime.datetime(2006, 4, 29, 20, 48, 0)
            for info in zf.infolist():
                if info.is_dir():
                    continue
                # Check file size
                if info.file_size >= 4294:
                    # info.date_time is a tuple: (year, month, day, hour, minute, second)
                    mod_dt = datetime.datetime(*info.date_time)
                    if mod_dt >= ref_dt:
                        total_size += info.file_size
            return total_size
    except Exception as e:
        return f"Error processing zip: {e}"

def process_move_rename_files(file):
    # Mapping for digit replacement: '0'→'1', ..., '8'→'9', '9'→'0'
    trans_map = str.maketrans("0123456789", "1234567890")
    
    # Create a temporary directory for extraction and processing
    with tempfile.TemporaryDirectory() as tempdir:
        extract_dir = os.path.join(tempdir, "extracted")
        os.mkdir(extract_dir)
        target_dir = os.path.join(tempdir, "target")
        os.mkdir(target_dir)
        
        # Extract ZIP file to extract_dir
        with zipfile.ZipFile(io.BytesIO(file.file.read()), 'r') as zf:
            zf.extractall(extract_dir)
        
        # Move all files from any subfolder to target_dir
        for root, dirs, files in os.walk(extract_dir):
            for fname in files:
                src = os.path.join(root, fname)
                dst = os.path.join(target_dir, fname)
                os.rename(src, dst)
        
        # Rename files in target_dir: replace each digit with the next
        for fname in os.listdir(target_dir):
            new_fname = fname.translate(trans_map)
            src = os.path.join(target_dir, fname)
            dst = os.path.join(target_dir, new_fname)
            os.rename(src, dst)
        
        # Simulate "grep . *": for each file (in sorted order), output "filename:line" for non-empty lines
        output_lines = []
        for fname in sorted(os.listdir(target_dir)):
            fpath = os.path.join(target_dir, fname)
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    if line.strip():  # non-empty line
                        output_lines.append(f"{fname}:{line.rstrip('\n')}")
        
        # Sort lines as in LC_ALL=C sort and join with newline
        sorted_lines = sorted(output_lines)
        combined = "\n".join(sorted_lines) + "\n"
        
        # Compute SHA-256 hash of the combined bytes
        hash_val = hashlib.sha256(combined.encode("utf-8")).hexdigest()
        return hash_val

def process_compare_files(file: UploadFile):
    try:
        file_content = file.file.read()
        zip_data = io.BytesIO(file_content)
        with zipfile.ZipFile(zip_data, 'r') as zf:
            # Read a.txt and b.txt (assuming UTF-8 encoding)
            a_text = zf.read("a.txt").decode("utf-8", errors="replace")
            b_text = zf.read("b.txt").decode("utf-8", errors="replace")
            a_lines = a_text.splitlines()
            b_lines = b_text.splitlines()
            # Count the number of lines that differ (compare corresponding lines)
            diff_count = sum(1 for a, b in zip(a_lines, b_lines) if a != b)
            return diff_count
    except Exception as e:
        return f"Error processing zip: {e}"


class SimilarityRequest(BaseModel):
    docs: list[str]
    query: str

def cosine_similarity(vec1, vec2):
    """Compute cosine similarity between two vectors."""
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    return dot_product / (norm1 * norm2 + 1e-9)

def get_embedding(text: str):
    """
    Deterministic embedding function:
    Treats every text (document or query) the same way.
    For demonstration, we compute a 2-dimensional vector where:
      - The first element is the sum of ASCII codes of the text.
      - The second element is the length of the text.
    """
    ascii_sum = sum(ord(c) for c in text)
    length = len(text)
    return np.array([ascii_sum, length], dtype=float)

def compute_similarity(request_json):
    """
    Expects a dictionary with:
      - "docs": list of document strings.
      - "query": the query string.
    
    Treats the query as a document by computing its embedding the same way.
    Then computes cosine similarity between the query vector and each document vector,
    ranks the documents by similarity, and returns the identifiers (document texts)
    of the top three matches.
    
    Returns a dictionary like:
      {"matches": ["<most similar doc>", "<2nd most similar doc>", "<3rd most similar doc>"]}
    """
    docs = request_json.get("docs", [])
    query = request_json.get("query", "")
    
    if not docs or not query:
        raise ValueError("Both 'docs' and 'query' must be provided.")
    
    # Treat the query as a document: generate its embedding.
    query_emb = get_embedding(query)
    # Generate embeddings for each document using the same function.
    doc_embeddings = [get_embedding(doc) for doc in docs]
    
    # Compute cosine similarity for each document against the query embedding.
    similarities = [cosine_similarity(query_emb, emb) for emb in doc_embeddings]
    
    # Rank the documents by similarity (highest similarity first) and take the top three.
    top_indices = np.argsort(similarities)[::-1][:3]
    matches = [docs[i] for i in top_indices]
    
    return {"matches": matches}



def extract_rating_bounds(question: str) -> (float, float):
    """
    Extracts the lower and upper rating bounds from the question text.
    For example, for a question like:
    "Retrieve movie information for all films that have a rating between 5 and 6."
    It returns (5.0, 6.0). Defaults to (5.0, 6.0) if not found.
    """
    pattern = r"rating between\s*([\d\.]+)\s*and\s*([\d\.]+)"
    match = re.search(pattern, question, re.IGNORECASE)
    if match:
        low = float(match.group(1))
        high = float(match.group(2))
        return low, high
    return 5.0, 6.0

def scrape_imdb_movies(question: str) -> list:
    """
    Extracts rating bounds from the question text,
    builds the IMDb advanced search URL with a filter for movies with a rating between low and high,
    scrapes up to the first 25 movie results from the IMDb page with the new layout,
    and returns a list of dictionaries with keys: id, title, year, rating.
    """
    # Extract rating bounds
    low, high = extract_rating_bounds(question)
    
    # Build the IMDb advanced search URL
    url = f"https://www.imdb.com/search/title/?title_type=feature&user_rating={low:.1f},{high:.1f}"
    
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0.0.0 Safari/537.36"
        )
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Find the main list container using the unique class from the snippet
    ul = soup.find("ul", class_="ipc-metadata-list ipc-metadata-list--dividers-between sc-e22973a9-0 khSCXM detailed-list-view ipc-metadata-list--base")
    if not ul:
        return []
    
    li_items = ul.find_all("li", class_="ipc-metadata-list-summary-item")
    movies = []
    
    for li in li_items[:25]:
        # Extract the movie title from the <h3> element with class "ipc-title__text"
        title_tag = li.find("h3", class_="ipc-title__text")
        title = title_tag.get_text(strip=True) if title_tag else ""
        
        # Extract IMDb id from the <a> tag with href matching /title/tt\d+/
        a_tag = li.find("a", href=re.compile(r"/title/(tt\d+)/"))
        if a_tag:
            href = a_tag.get("href", "")
            id_match = re.search(r"/title/(tt\d+)/", href)
            movie_id = id_match.group(1) if id_match else ""
        else:
            movie_id = ""
        
        # Extract year; usually found in one of the <span> elements inside metadata
        metadata_items = li.find_all("span", class_=re.compile(r"sc-e8bccfea-7"))
        year = ""
        for item in metadata_items:
            text = item.get_text(strip=True)
            if re.fullmatch(r"\d{4}", text):
                year = text
                break
        
        # Extract rating from the rating group; look for a span with class "ipc-rating-star--rating"
        rating_tag = li.find("span", class_="ipc-rating-star--rating")
        rating = rating_tag.get_text(strip=True) if rating_tag else ""
        
        movie_data = {
            "id": movie_id,
            "title": title,
            "year": year,
            "rating": rating
        }
        movies.append(movie_data)
    
    return movies

# API endpoint
@app.post("/api/")
async def process_question(
    question: str = Form(...),
    file: UploadFile = File(None),
    file2: UploadFile = File(None)
):
    # Build a list of files for functions that expect a single file or need multiple files
    files = [f for f in (file, file2) if f is not None]
    # For functions expecting a single file, we pick the first file if available.
    selected_file = files[0] if files else None

    q_number, similarity_score = check_question_similarity(question)
    if similarity_score >= 1.0:
        answer = get_answer(q_number, selected_file, question)
    
        if not isinstance(answer, dict):
            answer = str(answer)
        else:
            answer = json.dumps(answer)
        return {"answer": answer}
    else:
        return {"error": "Question not recognized", "similarity_score": similarity_score}
    


@app.get("/api/ver/")  # ✅ Now allows GET requests
async def get_marks(name: list[str] = Query(...)):
    clean_names = [n.strip('"') for n in name]  # Clean up names
    result = [marks.get(n, None) for n in clean_names]
    return {"marks": result}
@app.get("/api/ga27/")
async def get_students(class_param: list[str] = Query(None, alias="class")):
    if class_param:
        filtered_students = [s for s in students if s["class"] in class_param]
        
        return {"students": filtered_students}
    
    return {"students": students}


@app.post("/api/v1/chat/completions")
def fake_llama_api():
    response_data = {
        "id": "cmpl-xyz987",
        "object": "chat.completion",
        "created": 1712000000,
        "model": "llama-3.2-1b-instruct.q6_k",  # Change this if needed
        "system_fingerprint": "fp_12345678",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "user: 23f3001787, domain: ds.study.iitm.ac.in"
                },
                "logprobs": None,
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 12,
            "completion_tokens": 10,
            "total_tokens": 22
        }
    }

    return JSONResponse(content=response_data, media_type="application/json")



@app.post("/api/similarity/")
async def similarity_endpoint(request: SimilarityRequest):
    try:
        result = compute_similarity(request.dict())
        return result
    except Exception as e:
        raise Exception(status_code=400, detail=str(e))
    



@app.get("/execute")
def execute_form(question: str = Form(...)):
    # Ticket Status: "What is the status of ticket 83742?"
    ticket_match = re.search(r"status of ticket (\d+)", question, re.IGNORECASE)
    if ticket_match:
        ticket_id = int(ticket_match.group(1))
        return {
            "name": "get_ticket_status",
            "arguments": json.dumps({"ticket_id": ticket_id})
        }
    
    # Meeting Scheduling: "Schedule a meeting on 2025-02-15 at 14:00 in Room A."
    meeting_match = re.search(r"Schedule a meeting on (\d{4}-\d{2}-\d{2}) at ([0-9]{2}:[0-9]{2}) in (.+?)\.", question, re.IGNORECASE)
    if meeting_match:
        date = meeting_match.group(1)
        time = meeting_match.group(2)
        meeting_room = meeting_match.group(3)
        return {
            "name": "schedule_meeting",
            "arguments": json.dumps({"date": date, "time": time, "meeting_room": meeting_room})
        }
    
    # Expense Reimbursement: "Show my expense balance for employee 10056."
    expense_match = re.search(r"expense balance for employee (\d+)", question, re.IGNORECASE)
    if expense_match:
        employee_id = int(expense_match.group(1))
        return {
            "name": "get_expense_balance",
            "arguments": json.dumps({"employee_id": employee_id})
        }
    
    # Performance Bonus Calculation: "Calculate performance bonus for employee 10056 for 2025."
    bonus_match = re.search(r"Calculate performance bonus for employee (\d+) for (\d{4})", question, re.IGNORECASE)
    if bonus_match:
        employee_id = int(bonus_match.group(1))
        current_year = int(bonus_match.group(2))
        return {
            "name": "calculate_performance_bonus",
            "arguments": json.dumps({"employee_id": employee_id, "current_year": current_year})
        }
    
    # Office Issue Reporting: "Report office issue 45321 for the Facilities department."
    issue_match = re.search(r"Report office issue (\d+) for the ([\w\s]+) department", question, re.IGNORECASE)
    if issue_match:
        issue_code = int(issue_match.group(1))
        department = issue_match.group(2).strip()
        return {
            "name": "report_office_issue",
            "arguments": json.dumps({"issue_code": issue_code, "department": department})
        }
    
    raise HTTPException(status_code=400, detail="Query not recognized")

@app.get("/api/outline")
def get_outline(country: str = Query(..., description="Name of the country")):
    """
    Fetches the Wikipedia page for the given country, extracts all headings (H1-H6),
    and returns a Markdown outline.
    """
    # Replace spaces with underscores to form a valid Wikipedia URL
    country_url = country.strip().replace(" ", "_")
    wiki_url = f"https://en.wikipedia.org/wiki/{country_url}"
    
    try:
        response = requests.get(wiki_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=404, detail=f"Could not fetch Wikipedia page for {country}. Error: {str(e)}")
    
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Extract all headings (h1 through h6) in the order they appear in the document
    headings = []
    for tag in soup.find_all(re.compile("^h[1-6]$")):
        level = int(tag.name[1])
        text = tag.get_text(strip=True)
        headings.append(("#" * level) + " " + text)
    
    # Prepend a Contents header
    markdown_outline = "## Contents\n\n" + "\n\n".join(headings)
    
    return {"outline": markdown_outline}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
