# Book Cover Generator

An AI-powered book cover generator that creates multiple design variations based on book titles.

## System Workflow

1. **Input Stage**: User provides one or more book titles and configures generation parameters
2. **Description Generation**: The system uses GPT-4o to generate multiple unique cover descriptions for each book title
3. **Image Generation**: Each description is transformed into a high-quality book cover image using GPT-image-1
4. **Output & Storage**: Generated images are displayed in the UI and saved locally

## Features

- **Multi-title Processing**: Generate covers for multiple books in a single run
- **Description Variations**: Create 1-5 unique cover descriptions per book title
- **Image Quality Options**: Choose between standard and HD quality
- **Size Customization**: Select from multiple aspect ratios (square, landscape, portrait)
- **Local Storage**: All generated covers are saved to disk automatically
- **Easy Download**: Download any generated cover directly from the UI
- **Description Viewing**: See the AI-generated description used for each cover

## Installation & Setup

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd cover_generation
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. **API Key Setup** (REQUIRED):
   You NEED an OpenAI API key with access to GPT-4o and GPT-image-1 models. Set it up using one of these methods:
   
   - **Method 1**: Create a `.env` file in the project root:
     ```
     # Create a copy of .env.example
     cp .env.example .env
     
     # Edit the .env file and replace with your actual API key
     OPENAI_API_KEY=your_actual_api_key_here
     ```
   
   - **Method 2**: Set as environment variable in terminal:
     ```bash
     export OPENAI_API_KEY=your_actual_api_key_here
     ```
   
   - **Method 3**: Enter directly in the app when prompted (if not set using methods 1 or 2)

4. Run the application:
   ```bash
   streamlit run app.py
   ```
   
   This will start the app and open it in your web browser at http://localhost:8501

## Usage Guide

1. **Input Book Titles**:
   - Enter one or more book titles, with each title on a separate line
   - Example:
     ```
     The Midnight Library
     Project Hail Mary
     The Silent Patient
     ```

2. **Configure Generation Settings**:
   - **Number of variations**: How many different cover designs to create per book (1-5)
   - **Image quality**: Standard (faster) or HD (higher quality but slower)
   - **Image size**: Choose the aspect ratio that fits your book format

3. **Generate Covers**:
   - Click the "Generate Book Covers" button
   - If you haven't set up your API key via .env or environment variable, you'll be prompted to enter it

4. **View Results**:
   - Each book will have its own section with all generated cover variations
   - Click "View description" to see the AI-generated description used for that cover
   - Use the download buttons to save individual covers

5. **Find Saved Files**:
   - All generated covers are automatically saved to the `generated_covers` directory
   - Each book gets its own subfolder with images and description text files

## Costs & API Usage

- This application uses OpenAI's GPT-4o and GPT-image-1 models
- Both models incur API usage costs based on your OpenAI account
- Cost will vary based on the number of books, variations, and image quality settings

## Troubleshooting

- **API Key Errors**: Ensure your OpenAI API key is valid and has access to both required models
- **Generation Failures**: If image generation fails, try reducing the quality or using a different book title
- **Rate Limits**: The app includes small delays between requests to avoid rate limiting

## Requirements

- Python 3.8+
- OpenAI API key with access to GPT-4o and GPT-image-1 models
- Internet connection
