"""
Streamlit Web Interface for OTUS Joke Generator
Interactive web app for generating jokes
"""

import streamlit as st
from joke_generator import JokeGenerator
import time


# Page config
st.set_page_config(
    page_title="OTUS Joke Generator",
    page_icon="😂",
    layout="centered"
)


@st.cache_resource
def load_generator():
    """Load and cache the joke generator"""
    return JokeGenerator()


def main():
    """Main Streamlit app"""

    # Header
    st.title("😂 OTUS Joke Generator")
    st.markdown("*Generate jokes using GPT-2 AI model*")
    st.markdown("---")

    # Sidebar settings
    st.sidebar.header("⚙️ Settings")

    category = st.sidebar.selectbox(
        "Joke Category",
        options=['general', 'programming', 'dad_jokes', 'puns'],
        index=0,
        help="Select the type of joke to generate"
    )

    temperature = st.sidebar.slider(
        "Creativity (Temperature)",
        min_value=0.1,
        max_value=2.0,
        value=0.8,
        step=0.1,
        help="Higher = more creative and random"
    )

    max_length = st.sidebar.slider(
        "Max Length",
        min_value=50,
        max_value=200,
        value=100,
        step=10,
        help="Maximum number of tokens to generate"
    )

    num_jokes = st.sidebar.number_input(
        "Number of Jokes",
        min_value=1,
        max_value=5,
        value=1,
        help="Generate multiple jokes at once"
    )

    st.sidebar.markdown("---")
    use_custom = st.sidebar.checkbox("Use custom prompt", value=False)

    # Main content
    col1, col2 = st.columns([3, 1])

    with col1:
        st.subheader("🎭 Generate Your Joke")

    with col2:
        if st.button("🎲 Random", help="Generate with random category"):
            import random
            category = random.choice(['general', 'programming', 'dad_jokes', 'puns'])
            st.sidebar.success(f"Random: {category}")

    # Custom prompt input
    custom_prompt = None
    if use_custom:
        custom_prompt = st.text_area(
            "Custom Prompt",
            value="Write a funny joke about:",
            height=100,
            help="Enter your own prompt to guide joke generation"
        )

    # Generate button
    generate_button = st.button("🚀 Generate Joke!", type="primary", use_container_width=True)

    # Display area
    if generate_button:
        with st.spinner('🤖 AI is thinking of a joke...'):
            # Load generator
            generator = load_generator()

            # Generate jokes
            jokes = generator.batch_generate(
                category=category,
                num_jokes=num_jokes,
                temperature=temperature,
                max_length=max_length,
                custom_prompt=custom_prompt if use_custom else None
            )

            # Display results
            st.markdown("---")
            st.subheader("📝 Generated Jokes:")

            for i, joke in enumerate(jokes, 1):
                if num_jokes > 1:
                    st.markdown(f"**Joke {i}:**")

                # Display in a nice box
                st.info(joke)

                # Add copy button using code block
                with st.expander("📋 Copy joke"):
                    st.code(joke, language=None)

                time.sleep(0.1)  # Small delay for better UX

            # Success message
            st.success("✅ Joke(s) generated successfully!")

            # Regenerate button
            if st.button("🔄 Generate Another"):
                st.rerun()

    # Info section
    st.markdown("---")
    with st.expander("ℹ️ About this project"):
        st.markdown("""
        ### OTUS Joke Generator

        This is a demo project for the OTUS Python course (HW11).

        **Features:**
        - Multiple joke categories (programming, dad jokes, puns, general)
        - Adjustable creativity and length
        - Custom prompt support
        - Batch generation

        **Technology:**
        - Model: DistilGPT-2 (HuggingFace)
        - Framework: PyTorch + Transformers
        - Interface: Streamlit

        **Model Info:**
        - Base model: distilgpt2
        - Parameters: 82M
        - Architecture: GPT-2 (autoregressive)
        """)

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>"
        "Made with ❤️ for OTUS | Powered by GPT-2"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == '__main__':
    main()
