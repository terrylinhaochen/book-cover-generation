import streamlit as st
import os
import time
from openai import OpenAI
import base64
from PIL import Image
import io
import json
import urllib.parse
import uuid
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Initialize OpenAI client
client = OpenAI()

# Set page config
st.set_page_config(
    page_title="Book Cover Generator",
    page_icon="📚",
    layout="wide"
)

def generate_cover_descriptions(book_names: List[str], num_variations: int, custom_system_prompt: str = None) -> Dict[str, List[str]]:
    """
    Generate multiple cover descriptions for each book name using GPT-4o
    
    Args:
        book_names: List of book names
        num_variations: Number of description variations to generate per book
        custom_system_prompt: Optional custom system prompt to use instead of the default
        
    Returns:
        Dictionary mapping book names to lists of descriptions
    """
    descriptions = {}
    
    # Default system prompt
    default_system_prompt = """You are a skilled book cover designer specializing in simple, cartoonish art styles.
Create descriptions for book covers with a minimalist, flat design aesthetic using simple shapes, clean lines,
and solid background colors. Focus on creating playful, cartoonish imagery with limited detail. 
Your descriptions should specify:
- Simple character or object illustrations with minimal details
- Flat design with limited or no shading
- Bold, solid color backgrounds
- Clean, simple line art
- Minimalist composition focusing on a single central element or character
- A modern, playful aesthetic suitable for all audiences
Keep the description between 80-120 words."""
    
    # Use custom prompt if provided, otherwise use default
    system_prompt = custom_system_prompt if custom_system_prompt else default_system_prompt
    
    for book_name in book_names:
        descriptions[book_name] = []
        
        user_prompt = f"Create a detailed description for a book cover for a book titled: '{book_name}'"
        
        with st.spinner(f"Generating {num_variations} descriptions for '{book_name}'..."):
            for i in range(num_variations):
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.9,  # Higher temperature for more variation
                    )
                    description = response.choices[0].message.content
                    descriptions[book_name].append(description)
                    
                except Exception as e:
                    st.error(f"Error generating description {i+1} for '{book_name}': {e}")
                    
                # Add a small delay to avoid rate limits
                time.sleep(0.5)
                
    return descriptions

def generate_cover_images(descriptions: Dict[str, List[str]], 
                         image_quality: str,
                         image_size: str) -> Dict[str, List[Dict]]:
    """
    Generate book cover images based on descriptions using GPT-image-1
    
    Args:
        descriptions: Dictionary mapping book names to lists of descriptions
        image_quality: Quality setting for image generation (low, medium, high, or auto)
        image_size: Size of the generated images (1024x1024, etc.)
        
    Returns:
        Dictionary mapping book names to lists of image data (base64 and bytes)
    """
    images = {}
    
    for book_name, book_descriptions in descriptions.items():
        images[book_name] = []
        
        for i, description in enumerate(book_descriptions):
            try:
                with st.spinner(f"Generating image {i+1} for '{book_name}'..."):
                    # Enhance the prompt for a book cover
                    enhanced_prompt = f"""Book cover design for the book titled "{book_name}". 
                    {description}
                    The image should have the composition and style of a professional book cover 
                    with space for title and author text."""
                    
                    result = client.images.generate(
                        model="gpt-image-1",
                        prompt=enhanced_prompt,
                        size=image_size,
                        quality=image_quality,
                        n=1,
                    )
                    
                    image_base64 = result.data[0].b64_json
                    image_bytes = base64.b64decode(image_base64)
                    
                    images[book_name].append({
                        "b64_json": image_base64,
                        "bytes": image_bytes,
                        "description": description
                    })
            
            except Exception as e:
                st.error(f"Error generating image {i+1} for '{book_name}': {e}")
            
            # Add a small delay to avoid rate limits
            time.sleep(1)
    
    return images

def save_images(images: Dict[str, List[Dict]], output_dir: str = "generated_covers"):
    """
    Save generated images to disk
    
    Args:
        images: Dictionary of generated images
        output_dir: Directory to save images
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    for book_name, book_images in images.items():
        # Create book-specific directory
        book_dir = os.path.join(output_dir, book_name.replace(" ", "_"))
        os.makedirs(book_dir, exist_ok=True)
        
        # Save each image and its description
        for i, img_data in enumerate(book_images):
            # Save image
            img_path = os.path.join(book_dir, f"cover_{i+1}.png")
            with open(img_path, "wb") as f:
                f.write(img_data["bytes"])
            
            # Save description
            desc_path = os.path.join(book_dir, f"description_{i+1}.txt")
            with open(desc_path, "w") as f:
                f.write(img_data["description"])
    
    return output_dir

def display_images(images: Dict[str, List[Dict]]):
    """Display generated images in the Streamlit UI"""
    for book_name, book_images in images.items():
        st.header(f"Cover designs for: {book_name}")
        
        # Check if we have any successful image generations
        if len(book_images) == 0:
            st.warning(f"No images were successfully generated for '{book_name}'.")
            continue
            
        # Use columns to display images side by side
        cols = st.columns(min(3, max(1, len(book_images))))
        
        for i, img_data in enumerate(book_images):
            col_idx = i % len(cols)
            with cols[col_idx]:
                # Convert bytes to PIL Image
                img = Image.open(io.BytesIO(img_data["bytes"]))
                st.image(img, caption=f"Cover {i+1}", use_container_width=True)
                
                with st.expander("View description"):
                    st.write(img_data["description"])
                
                # Download button for each image
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                btn = st.download_button(
                    label=f"Download Cover {i+1}",
                    data=buf.getvalue(),
                    file_name=f"{book_name.replace(' ', '_')}_cover_{i+1}.png",
                    mime="image/png"
                )

def encode_config_to_url(config):
    """Encode configuration to URL parameters"""
    # Encode system prompt to base64 to avoid URL encoding issues
    encoded_prompt = base64.b64encode(config["system_prompt"].encode()).decode()
    
    # Encode book names if present
    book_names_str = ""
    if "book_names" in config and config["book_names"]:
        book_names_str = "|".join(config["book_names"])
        book_names_str = base64.b64encode(book_names_str.encode()).decode()
    
    params = {
        "prompt": encoded_prompt,
        "variations": config["num_variations"],
        "quality": config["image_quality"],
        "size": config["image_size"]
    }
    
    # Add book names if available
    if book_names_str:
        params["books"] = book_names_str
    
    # Generate parameters string
    param_str = "&".join([f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items()])
    return param_str

def decode_config_from_params(params):
    """Decode configuration from URL parameters"""
    config = {}
    
    if "prompt" in params:
        try:
            # Decode base64 encoded prompt
            encoded_prompt = params["prompt"]
            config["system_prompt"] = base64.b64decode(encoded_prompt).decode()
        except:
            config["system_prompt"] = None
    
    if "variations" in params:
        try:
            config["num_variations"] = int(params["variations"])
        except:
            config["num_variations"] = 1  # Updated default to 1
    
    if "quality" in params:
        config["image_quality"] = params["quality"]
    
    if "size" in params:
        config["image_size"] = params["size"]
        
    # Extract book names if present
    if "books" in params:
        try:
            encoded_books = params["books"]
            books_str = base64.b64decode(encoded_books).decode()
            config["book_names"] = books_str.split("|") if books_str else []
        except:
            config["book_names"] = []
    
    return config

def main():
    # Initialize session state for storing images across reruns
    if 'images' not in st.session_state:
        st.session_state['images'] = None
    
    st.title("📚 Book Cover Generator")
    st.write("Generate multiple book cover designs using AI")
    
    # Default config values
    default_system_prompt = """You are a skilled book cover designer specializing in simple, cartoonish art styles.
Create descriptions for book covers with a minimalist, flat design aesthetic using simple shapes, clean lines,
and solid background colors. Focus on creating playful, cartoonish imagery with limited detail. 
Your descriptions should specify:
- Simple character or object illustrations with minimal details
- Flat design with limited or no shading
- Bold, solid color backgrounds
- Clean, simple line art
- Minimalist composition focusing on a single central element or character
- A modern, playful aesthetic suitable for all audiences
Keep the description between 80-120 words."""
    
    default_config = {
        "system_prompt": default_system_prompt,
        "num_variations": 1,
        "image_quality": "medium",
        "image_size": "1024x1024"
    }
    
    # Check for URL parameters
    query_params = st.query_params
    config_from_url = decode_config_from_params(query_params)
    
    # Merge defaults with URL params
    config = {**default_config, **{k: v for k, v in config_from_url.items() if v is not None}}
    
    # Admin settings (only shown when admin=true in URL)
    if "admin" in query_params and query_params["admin"] == "true":
        with st.expander("⚙️ Administrator Settings", expanded=True):
            st.write("These settings are for server administrators.")
            
            base_url = st.text_input(
                "Deployment URL:",
                value=os.environ.get("SHARE_BASE_URL", "http://localhost:8501"),
                help="The base URL where this app is deployed. Used for generating shareable links."
            )
            
            if st.button("Save Settings"):
                # In a real deployment, these would be saved in a more persistent way
                os.environ["SHARE_BASE_URL"] = base_url
                st.success("Settings saved!")
                st.info("Note: These settings are temporary and will be lost when the server restarts. For permanent settings, set environment variables.")
                
                # Generate a link to exit admin mode
                st.markdown(f"[Exit Admin Mode]({base_url})")
    
    with st.form("book_input_form"):
        # Multiple book names input
        book_names_text = st.text_area(
            "Enter book name(s), one per line:",
            value="" if "book_names" not in config else "\n".join(config["book_names"]),
            help="Enter one or more book names, with each name on a new line."
        )
        
        # Configuration options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            num_variations = st.slider(
                "Number of variations per book:",
                min_value=1,
                max_value=5,
                value=config["num_variations"],
                help="Number of different cover designs to generate for each book"
            )
        
        with col2:
            image_quality = st.selectbox(
                "Image quality:",
                options=["low", "medium", "high", "auto"],
                index=["low", "medium", "high", "auto"].index(config["image_quality"]) if config["image_quality"] in ["low", "medium", "high", "auto"] else 1,
                help="Higher quality images may take longer to generate"
            )
        
        with col3:
            image_size = st.selectbox(
                "Image size:",
                options=["1024x1024", "1024x1536", "1536x1024", "auto"],
                index=["1024x1024", "1024x1536", "1536x1024", "auto"].index(config["image_size"]) if config["image_size"] in ["1024x1024", "1024x1536", "1536x1024", "auto"] else 0,
                help="Choose image dimensions (width x height)"
            )
            
        # Advanced options section - renamed to Prompt Configurations
        with st.expander("Prompt Configurations"):
            custom_system_prompt = st.text_area(
                "Customize description generation prompt:",
                value=config["system_prompt"],
                height=200,
                help="Customize the system prompt used to generate cover descriptions. This affects the style and content of the descriptions."
            )
        
        # Submit button
        submitted = st.form_submit_button("Generate Book Covers")
    
    # Generate configuration URL after the form
    book_names = [name.strip() for name in book_names_text.split("\n") if name.strip()]
    
    current_config = {
        "system_prompt": custom_system_prompt,
        "num_variations": num_variations,
        "image_quality": image_quality,
        "image_size": image_size,
        "book_names": book_names
    }
    
    # Only show sharing section if the config differs from default or if config was loaded from URL
    config_is_custom = (current_config["system_prompt"].strip() != default_config["system_prompt"].strip() or
                       current_config["num_variations"] != default_config["num_variations"] or
                       current_config["image_quality"] != default_config["image_quality"] or
                       current_config["image_size"] != default_config["image_size"] or
                       bool(config_from_url))
    
    if config_is_custom:
        with st.expander("Share Configuration"):
            param_str = encode_config_to_url(current_config)
            base_url = st.text_input("Base URL (edit if needed):", 
                                    value=os.environ.get("SHARE_BASE_URL", "http://localhost:8501"))
            
            shareable_url = f"{base_url}?{param_str}"
            
            st.code(shareable_url, language="text")
            
            # Use JavaScript to copy to clipboard without page refresh
            st.markdown("""
            <div id="copy-button-container">
                <button id="copy-button" style="background-color:#4CAF50; color:white; border:none; padding:10px 20px; text-align:center; text-decoration:none; display:inline-block; font-size:16px; margin:4px 2px; cursor:pointer; border-radius:4px;">
                    Copy Shareable Link
                </button>
                <span id="copy-success" style="display:none; color:green; margin-left:10px;">✓ Copied to clipboard!</span>
            </div>
            
            <script>
                const copyButton = document.getElementById('copy-button');
                const copySuccess = document.getElementById('copy-success');
                const textToCopy = `""" + shareable_url + """`;
                
                copyButton.addEventListener('click', function() {
                    navigator.clipboard.writeText(textToCopy).then(function() {
                        copySuccess.style.display = 'inline';
                        
                        // Show Streamlit toast notification
                        window.parent.postMessage({
                            type: 'streamlit:showSuccessToast',
                            message: 'Configuration link copied to clipboard!'
                        }, '*');
                        
                        setTimeout(function() {
                            copySuccess.style.display = 'none';
                        }, 2000);
                    });
                });
            </script>
            """, unsafe_allow_html=True)
    
    if submitted:
        # Process the book names input
        book_names = [name.strip() for name in book_names_text.split("\n") if name.strip()]
        
        if not book_names:
            st.error("Please enter at least one book name.")
            return
        
        # Check if OpenAI API key is set
        if not os.environ.get("OPENAI_API_KEY") and not client.api_key:
            # Show API key input if not set
            api_key = st.text_input("Enter your OpenAI API key:", type="password")
            if api_key:
                os.environ["OPENAI_API_KEY"] = api_key
                client.api_key = api_key
            else:
                st.error("OpenAI API key is required.")
                return
        
        # Display the books to be processed
        st.write(f"Generating covers for {len(book_names)} book(s):")
        for name in book_names:
            st.write(f"- {name}")
        
        # Check if custom prompt is different from default
        if custom_system_prompt.strip() != default_config["system_prompt"].strip():
            st.info("Using custom description generation prompt.")
            custom_prompt_to_use = custom_system_prompt
        else:
            custom_prompt_to_use = None
        
        # Step 1: Generate descriptions
        descriptions = generate_cover_descriptions(
            book_names, 
            num_variations,
            custom_system_prompt=custom_prompt_to_use
        )
        
        # Step 2: Generate images
        images = generate_cover_images(
            descriptions, 
            image_quality=image_quality,
            image_size=image_size
        )
        
        # Step 3: Save images locally
        output_dir = save_images(images)
        st.success(f"All images saved to '{output_dir}' directory!")
        
        # Store the generated images in session state
        st.session_state['images'] = images
        
        # Step 4: Display images in the UI
        display_images(images)
    
    # If we have images in session state but form wasn't submitted, display them
    # This ensures images persist after UI interactions that cause reruns
    elif st.session_state['images'] is not None:
        st.success("Displaying previously generated covers. Submit the form again to generate new covers.")
        display_images(st.session_state['images'])

if __name__ == "__main__":
    main() 