# MindFort


## Usage

1. Install dependencies with `pip install -r requirements.txt` 
2. Run MindFort with `python app.py`
3. Navigate to `http://127.0.0.1:8000`
4. [Obtain](https://help.openai.com/en/articles/4936850-where-do-i-find-my-openai-api-key) and enter your OpenAI API key
5. Follow the on-screen instructions to load your input data, your codeset, perform coding and analyse your results
6. Find your results in the `/output` folder and on-screen. The used prompts are also saved in `/output/prompts.csv`

With any questions, feel free to contact me at [daniel.szabo@oulu.fi](mailto:daniel.szabo@oulu.fi)

### Docker

If you prefer to run MindFort as a docker container, you can build the image and run it as follows:

1. Build image with `docker build --tag mindfort .`
2. Run image with `docker run -d -p 8000:5000 mindfort` where 8000 is the port you will access the application at `http://127.0.0.1:8000`