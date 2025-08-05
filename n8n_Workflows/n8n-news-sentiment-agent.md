## **🧠 AI News Sentiment Workflow with n8n**

### **🔁 Workflow Overview**

This n8n workflow fetches AI-related news, applies simple sentiment tagging using Python, and alerts the user if any article is potentially negative. The steps:

1. **Schedule Trigger** – runs daily.

2. **Edit Fields** – allows configuration if needed.

3. **HTTP Request** – pulls headlines from NewsAPI.

4. **Split Out** – processes each article individually.  
5. **Python Code** – classifies sentiment based on keywords in the title:

`title = item.get("json", {}).get("title", "").lower()`

`if "gain" in title or "raise" in title:`  
    `sentiment = "positive"`  
`elif "loss" in title or "drop" in title or "fall" in title:`  
    `sentiment = "negative"`  
`else:`  
    `sentiment = "neutral"`

`return {`  
    `"json": {`  
        `"title": item["json"]["title"],`  
        `"sentiment": sentiment,`  
        `"source": item["json"]["source"]["name"],`  
        `"publishedAt": item["json"]["publishedAt"],`  
        `"url": item["json"]["url"]`  
    `}`  
`}`

6. **Create Record** – stores results in Airtable.

7. **Filter** – keeps only the ones marked as "negative".

8. **Send Email** – sends alert if negative article is found.

🟢 The flow only sends an email when at least one negative item is detected.

---

### **🐍 Wrapping Python Inside n8n**

* The Python logic runs inside the `Code` node, which supports Python execution per item.

* No need to call an external script — everything is done natively in n8n.

* Helps automate tagging/classification efficiently.

---

**Why n8n was a Great Choice**

* **Visual-first Logic Building**: Unlike Airflow, which is more code-centric, n8n provides an intuitive, drag-and-drop UI based on React Flow.  
* **Rapid Debugging**: You can inspect outputs at each node, which made troubleshooting much easier.  
* **Lower Barrier for Entry**: For newer contributors or those with less Python/Airflow experience, n8n is significantly easier to understand.  
* **Integrated Connectors**: Built-in nodes for HTTP requests, email, Airtable, and more helped us move faster without writing boilerplate code.

---

## **🔧 Tool Use Cases**

### **🧩 React Flow**

* Frontend JS library used for building node-based visual editors (like what n8n already has).

* Best for creating user-facing drag-and-drop UIs.

### **⚙️ Apache Airflow**

* Backend orchestration tool to schedule and manage complex workflows, data pipelines, etc.

* Ideal for production ETL and time-based job orchestration.

🔍 **Observation**: These tools are not alternatives, but standalone with distinct use cases. React Flow is for frontend UI design. Airflow is for backend logic orchestration.

---

## **💡 Key Learnings**

* You can wrap Python directly inside n8n and use it for real-time decision-making.

* Low-code tools like n8n can still support custom logic via scripting.

* Airtable is easy to plug in for data logging without setting up a full database.

* Filtering and email notifications are built-in and intuitive.

