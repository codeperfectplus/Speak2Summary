# Speak2Summary

**Speak2Summary** is a Flask-based web application that leverages Large Language Models (LLMs) to transcribe and summarize meeting audio files. It provides an intuitive interface for users to upload audio recordings and receive concise summaries, facilitating efficient meeting reviews and note-taking.

## Features

* 🎙️ **Audio Transcription**: Convert spoken content from meetings into text using advanced speech-to-text capabilities.
* 🧠 **Summarization with LLMs**: Generate concise summaries of transcribed text utilizing powerful language models.
* Mind Map Generation: Create visual representations of meeting summaries to enhance understanding and retention.
* 🖥️ **User-Friendly Interface**: Interact with a clean and responsive web UI built with Flask.
* 🐳 **Dockerized Deployment**: Easily deploy the application using Docker and Docker Compose for a consistent environment setup.

## Prerequisites

* [Docker](https://www.docker.com/get-started) and [Docker Compose](https://docs.docker.com/compose/install/) installed on your system.
* Valid API keys for:

  * [GROQ API](https://groq.com/)
  * [OpenAI API](https://openai.com/api/)

## Installation and Usage

1. **Clone the Repository**

   ```bash
   git clone https://github.com/codeperfectplus/Speak2Summary.git
   ```



2. **Navigate to the Project Directory**

   ```bash
   cd Speak2Summary
   ```



3. **Set Environment Variables**

   Export your API keys as environment variables:

   ```bash
   export GROQ_API_KEY=your_groq_api_key
   export OPENAI_API_KEY=your_openai_api_key
   ```



*Replace `your_groq_api_key` and `your_openai_api_key` with your actual API keys.*

4. **Build and Run the Docker Container**

   Use Docker Compose to build and start the application:

   ```bash
   docker-compose up --build -d
   ```



5. **Access the Application**

   Open your web browser and navigate to:

   ```
   http://localhost:5000
   ```

## Screenshots

<!-- -rw-rw-r-- 1 admin admin 233969 May 29 08:12 'Screenshot from 2025-05-29 08-12-24.png'
-rw-rw-r-- 1 admin admin 237619 May 29 08:12 'Screenshot from 2025-05-29 08-12-59.png'
-rw-rw-r-- 1 admin admin 333019 May 29 08:14 'Screenshot from 2025-05-29 08-14-11.png'
-rw-rw-r-- 1 admin admin 240017 May 29 08:16 'Screenshot from 2025-05-29 08-16-20.png' -->

![Screenshot from 2025-05-29 08-12-24](src/screenshots/Screenshot%20from%202025-05-29%2008-12-24.png)
![Screenshot from 2025-05-29 08-12-59](src/screenshots/Screenshot%20from%202025-05-29%2008-12-59.png)
![Screenshot from 2025-05-29 08-14-11](src/screenshots/Screenshot%20from%202025-05-29%2008-14-11.png)
![Screenshot from 2025-05-29 08-16-20](src/screenshots/Screenshot%20from%202025-05-29%2008-16-20.png)


## License

This project is licensed under the [MIT License](LICENSE).

## Acknowledgments

* [Flask](https://flask.palletsprojects.com/) - Web framework used for the application.
* [OpenAI](https://openai.com/) - Provider of the language models used for summarization and transcription.
* [GROQ](https://groq.com/) - API used for audio transcription and Summarization.

## Contributing

We welcome contributions to Speak2Summary! If you have suggestions for improvements or new features, please open an issue or submit a pull request.
