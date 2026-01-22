# MindFort

MindFort is an educational platform designed to build resilience against misinformation through cognitive inoculation. It features an interactive chat experience with **Forty**, an AI character who challenges your beliefs to help you strengthen them.

## Dual Modes

- **Public Mode (`/`)**: A simplified, guest-accessible educational flow for general users.
- **Researcher Mode (`/study`)**: The original 5-stage research study version (requires sign-in).

## Usage

### 1-Command Run (Docker Compose)
The easiest way to run the whole project is using Docker Compose:
```bash
docker-compose up
```
Navigate to `http://127.0.0.1:8000` to see the public landing page.

### Manual Setup
1. Install dependencies: `pip install -r requirements.txt` 
2. Run the application: `python app.py`
3. [Obtain](https://help.openai.com/en/articles/4936850-where-do-i-find-my-openai-api-key) and enter your OpenAI API key in `chatgpt.py`.

### Database
The project uses SQLite. The database is stored in the `database/` directory.

---
Contact: [anonymous@anonymous.com](mailto:anonymous@anonymous.com)