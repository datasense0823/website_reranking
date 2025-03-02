import requests
from bs4 import BeautifulSoup
import json
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# Load environment variables
load_dotenv()

# Set API Keys (Use Free SERPAPI Key)
SERPAPI_KEY = "Enter Your Key"  # Get from https://serpapi.com/manage-api-key

# Initialize OpenAI LLM (Latest LangChain Version)
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

### **1️⃣ Extract Content from a Webpage**
def extract_text_from_html(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.find("title").text.strip() if soup.find("title") else ""
        paragraphs = [p.text.strip() for p in soup.find_all("p") if p.text.strip()]

        content = title + "\n" + " ".join(paragraphs)
        return content if content else "No meaningful text found on the page."

    except requests.exceptions.RequestException as e:
        print(f"⚠ Error fetching URL: {e}")
        return ""

### **2️⃣ Summarize the Content Using LLM**
def generate_summary(content):
    prompt = f"""
    Summarize the following article in **5 concise sentences**, highlighting the **core topic** and key points.

    **Article:**
    {content}

    **Summary Output:**
    """

    response = llm.invoke([HumanMessage(content=prompt)])

    return response.content.strip() if response else "No summary available."

### **3️⃣ Generate Top 10 SEO-Optimized Headings**
def generate_seo_headings(summary):
    prompt = f"""
    Based on the **article summary** below, generate **10 SEO-optimized headings** that:
    - Are **highly relevant** to the article content.
    - Include **powerful SEO keywords** to attract search traffic.
    - Follow the format: **H1 or H2 headings** (e.g., "Why India Lost the Cricket World Cup 2023")

    **Article Summary:**
    {summary}

    **Return format (Valid JSON List, NO extra text):**
    ```json
    ["Heading 1", "Heading 2", ..., "Heading 10"]
    ```
    """

    response = llm.invoke([HumanMessage(content=prompt)])

    # Ensure output is strictly valid JSON
    text = response.content.strip()
    text = text.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        print("⚠ LLM failed to generate valid JSON. Using fallback.")
        return [f"Fallback SEO Heading {i+1}" for i in range(10)]

### **4️⃣ Extract Top 10 SEO Search Terms from Summary**
def generate_search_terms(summary):
    prompt = f"""
    Based on the **article summary** below, generate **exactly 10 SEO-optimized search terms** that people might search for on Google.

    **Article Summary:**
    {summary}

    **Return format (Valid JSON List, NO extra text):**
    ```json
    ["search term 1", "search term 2", ..., "search term 10"]
    ```
    """

    response = llm.invoke([HumanMessage(content=prompt)])

    text = response.content.strip()
    text = text.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        print("⚠ LLM failed to generate valid JSON. Using fallback.")
        return [f"fallback search {i+1}" for i in range(10)]

### **5️⃣ Fetch Real-Time SEO Keywords Using SERPAPI**
def fetch_seo_keywords(search_terms):
    seo_keywords = {}

    for term in search_terms:
        print(f"🔍 Fetching SEO data for: {term}")

        url = f"https://serpapi.com/search.json?engine=google_autocomplete&q={term}&api_key={SERPAPI_KEY}"

        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                keywords = response.json().get("suggestions", [])
                seo_keywords[term] = [kw['value'] for kw in keywords if 'value' in kw][:5]  # ✅ Store top 5 related SEO keywords
            else:
                print(f"⚠ API Error for '{term}': {response.status_code}")
        except requests.exceptions.RequestException:
            print(f"⚠ Connection error while fetching keywords for {term}")

    return seo_keywords

### **6️⃣ Re-Rank SEO Headings with Optimized Keywords**
def regenerate_seo_headings_with_keywords(original_headings, seo_keywords):
    prompt = f"""
    Improve the **10 SEO headings** below by ensuring they **contain the most optimized keywords** extracted from SEO research.

    **Original SEO-Optimized Headings:**
    {json.dumps(original_headings, indent=2)}

    **SEO Keywords Extracted:**
    {json.dumps(seo_keywords, indent=2)}

    **Return format (Valid JSON List, NO extra text):**
    ```json
    ["Improved Heading 1", "Improved Heading 2", ..., "Improved Heading 10"]
    ```
    """

    response = llm.invoke([HumanMessage(content=prompt)])

    text = response.content.strip()
    text = text.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        print("⚠ Failed to generate improved headings. Using fallback.")
        return [f"Fallback Optimized Heading {i+1}" for i in range(10)]

### **7️⃣ Save Final SEO Data to JSON**
def save_seo_results(url, final_headings, final_keywords, filename="seo_final_results.json"):
    data = {"url": url, "final_headings": final_headings, "seo_keywords": final_keywords}
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    print(f"\n✅ SEO results saved to {filename}")

### **8️⃣ Execute Full Workflow**
if __name__ == "__main__":
    url = "https://www.bbc.com/news/world-asia-india-67471098"  # Replace with any valid URL
    content = extract_text_from_html(url)

    if content:
        print("\n🔹 Extracting content & generating summary...")
        summary = generate_summary(content)

        print("\n🔹 Generating initial SEO headings...")
        seo_headings = generate_seo_headings(summary)

        print("\n🔹 Extracting SEO search terms...")
        search_terms = generate_search_terms(summary)

        print("\n🔹 Fetching real-time SEO keywords using SERPAPI...")
        seo_keywords = fetch_seo_keywords(search_terms)

        print("\n🔹 Re-ranking SEO headings based on optimized keywords...")
        final_headings = regenerate_seo_headings_with_keywords(seo_headings, seo_keywords)

        print("\n🔹 **Final Top 10 SEO-Optimized Headings:**")
        for i, heading in enumerate(final_headings, 1):
            print(f"{i}. {heading}")

        # Save results
        save_seo_results(url, final_headings, seo_keywords)

    else:
        print("⚠ No content retrieved from the page.")
