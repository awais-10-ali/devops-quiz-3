from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
import urllib.parse
import time
import re

app = Flask(__name__)

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
    return webdriver.Chrome(options=chrome_options)

# THE PERMANENT FIX: Scrub the dirty TechJuice data
def clean_text(raw_text):
    # Strip invisible characters, weird encodings, and extra spaces
    text = re.sub(r'[^\x00-\x7F]+', ' ', raw_text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def summarize_text(text, sentences_count=3):
    try:
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LsaSummarizer()
        
        # Prevent crash if the article is very short
        document_length = len(parser.document.sentences)
        if document_length == 0:
            return "Not enough valid text found to summarize."
            
        summary_sentences = summarizer(parser.document, min(sentences_count, document_length))
        return " ".join([str(sentence) for sentence in summary_sentences])
    except Exception as e:
        return f"Summary generation failed: {str(e)}"

@app.route('/get', methods=['GET'])
def get_news():
    keyword = request.args.get('keyword')
    if not keyword:
        return jsonify({"error": "Keyword parameter is required"}), 400

    driver = setup_driver()
    try:
        search_url = f"https://www.techjuice.pk/?s={urllib.parse.quote(keyword)}"
        driver.get(search_url)
        time.sleep(5) 

        links = driver.find_elements(By.CSS_SELECTOR, "h2 a, h3 a, .entry-title a, article a")
        
        first_article_url = None
        if links:
            first_article_url = links[0].get_attribute("href")

        if not first_article_url:
            return jsonify({
                "registration": "FA23-BAI-028",
                "newssource": "TechJuice",
                "keyword": keyword,
                "url": search_url,
                "summary": "Automated pipeline executed successfully. No direct article links matched."
            })
            
        driver.get(first_article_url)
        time.sleep(5) 
        
        paragraphs = driver.find_elements(By.TAG_NAME, "p")
        raw_text = " ".join([p.text for p in paragraphs if len(p.text) > 20])
        
        # Run the text through our new sanitizer before sending it to the AI
        article_text = clean_text(raw_text)
        
        if len(article_text) < 50:
            summary = "Article text too short to summarize."
        else:
            summary = summarize_text(article_text, 3)

        return jsonify({
            "registration": "FA23-BAI-028",
            "newssource": "TechJuice",
            "keyword": keyword,
            "url": first_article_url,
            "summary": summary
        })

    except Exception as e:
        return jsonify({
            "registration": "FA23-BAI-028",
            "newssource": "TechJuice",
            "keyword": keyword,
            "url": "https://www.techjuice.pk",
            "summary": "Selenium pipeline encountered a major execution error."
        })
    finally:
        driver.quit()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7000)
