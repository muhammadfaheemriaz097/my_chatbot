# ✦ Feemo AI ✦
**A High-Performance, Stateful AI Assistant with Private Persistence.**
Feemo AI is a professional-grade chatbot interface built to demonstrate the integration of high-speed LLM inference with a cloud-based relational database. Unlike standard stateless chatbots, Feemo AI remembers your conversations across sessions while maintaining strict data isolation between different users.
## 🚀 Technical Architecture
* **LLM Engine:** [Groq LPU Inference](https://groq.com/) using Llama-3.3-70B for near-instant responses.
* **Backend / Database:** [Supabase](https://supabase.com/) (PostgreSQL) for storing chat history as `jsonb` material.
* **Framework:** [Streamlit](https://streamlit.io/) for a responsive, reactive web interface.
* **Identity Management:** UUID-based session tracking for private history without mandatory login.

## ✨ Key Features

* **⚡ Ultra-Fast Inference:** Leverages Groq's LPU technology to provide a streaming experience with zero lag.
* **💾 Persistent "Material" Storage:** Automatically saves full conversation history to a PostgreSQL database.
* **🔒 Built-in Privacy:** Each user is assigned a unique, persistent ID. History is isolated, ensuring one person cannot see another’s "Recent Activity."
* **📱 Mobile-First Design:** Custom CSS overrides to hide standard Streamlit UI elements, providing a clean, "app-like" experience on mobile browsers.
* **🔄 Stateful Reloads:** Uses URL query parameters to maintain user identity even after browser refreshes.

## 🛠️ Installation & Setup

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/feemo-ai.git

```
2. **Install dependencies:**
```bash
pip install streamlit supabase requests

3. **Configure Secrets:**
Create a `.streamlit/secrets.toml` file with your credentials:
```toml
SUPABASE_URL = "your_supabase_url"
SUPABASE_KEY = "your_supabase_anon_key"
GROQ_API_KEY = "your_groq_api_key"

4. **Run the app:**
```bash
streamlit run app.py

## 👨‍💻 Author

**Muhammad Faheem Riaz** *ML & AI Engineer* 
