"""
# Line Chatbot with AI-Powered Responses

This repository contains the source code for a Line chatbot that leverages AI to provide intelligent responses to user messages. The bot can handle text, audio, and image messages, offering a conversational experience with follow-up questions and the ability to clear conversation history.

## Features

- **Text Message Handling**: Processes user text messages and generates AI-driven responses with suggested follow-up questions.
- **Audio Message Handling**: Transcribes audio messages and processes the text to generate responses.
- **Image Message Handling**: Uploads images to AWS S3 and processes them to generate descriptions and follow-up questions.
- **Conversation History Management**: Users can clear their conversation history by sending \`0\`.
- **Quick Replies**: Provides quick reply options for users to select follow-up questions.

## Prerequisites

- Python 3.7 or higher
- A Line Messaging API account with Channel Access Token and Channel Secret
- AWS account with S3 bucket access
- Required Python packages (see [Requirements](#requirements))

## Getting Started

### Clone the Repository

\`\`\`bash
git clone https://github.com/yourusername/line-chatbot.git
cd line-chatbot
\`\`\`

### Requirements

Install the required Python packages:

\`\`\`bash
pip install -r requirements.txt
\`\`\`

### Configuration

Create a \`config.py\` file in the root directory with the following content:

\`\`\`python
class Config:
    CHANNEL_ACCESS_TOKEN = 'YOUR_CHANNEL_ACCESS_TOKEN'
    CHANNEL_SECRET = 'YOUR_CHANNEL_SECRET'
    AWS_ACCESS_KEY_ID = 'YOUR_AWS_ACCESS_KEY_ID'
    AWS_SECRET_ACCESS_KEY = 'YOUR_AWS_SECRET_ACCESS_KEY'
    S3_BUCKET = 'YOUR_S3_BUCKET_NAME'
    PORT = 8000  # Or any port you prefer
\`\`\`

Replace the placeholder values with your actual credentials.

### Run the Application

\`\`\`bash
python app.py
\`\`\`

The application will start running on \`http://0.0.0.0:8000/\` (or the port you specified).

### Expose the Application

To receive webhooks from Line, your application needs to be accessible from the internet. You can use tools like [ngrok](https://ngrok.com/) to expose your local server.

\`\`\`bash
ngrok http 8000
\`\`\`

## Usage

- Send any text, audio, or image message to interact with the bot.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue to discuss improvements or features.

"""