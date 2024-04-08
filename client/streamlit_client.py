import os
import requests
from PIL import Image
import numpy as np
from scipy.spatial.distance import cosine
import streamlit as st
from io import BytesIO
import base64
import plotly.graph_objects as go

# URL Endpoint
api_url = "http://api:8000/upload_image"

# Set page title
st.set_page_config(page_title="Image Similarity App")

# Add a title
st.title("Image Similarity App")

# Create a file uploader for the reference image
reference_image_file = st.file_uploader("Select the reference image", type=["jpg", "jpeg", "png"])

# Create a text input for the image directory path
image_directory = st.text_input("Enter the directory path containing other images")

# Create a slider for similarity score threshold
similarity_threshold = st.slider("Similarity Score Threshold", 0.0, 1.0, 0.5, 0.1)

if reference_image_file is not None and image_directory:
    # Load the reference image
    reference_image = Image.open(reference_image_file)
    reference_image_filename = reference_image_file.name

    # Create a list to store other images
    other_images = []

    # Iterate over the files in the selected directory
    for filename in os.listdir(image_directory):
        # skip the reference image if it is in the same directory
        if filename == reference_image_filename:
            continue

        # load the other images from the directory
        image_path = os.path.join(image_directory, filename)
        image = Image.open(image_path)
        other_images.append(image)

    # Prepare files for API request
    files = [("reference_image", (reference_image_filename, reference_image_file.getvalue(), "image/jpeg"))]
    files.extend([("images", (image.filename, open(os.path.join(image_directory, image.filename), "rb"), "image/jpeg")) for image in other_images])

    # Send API request
    response = requests.post(api_url, files=files)

    # Check the response status code
    if response.status_code == 200:
        try:
            result = response.json()
            reference_embedding = result["reference_embedding"]
            other_embeddings = [np.array(embedding_data["embedding"]) for embedding_data in result["other_embeddings"]]
            other_filenames = [os.path.basename(embedding_data["id"]) for embedding_data in result["other_embeddings"]]

            similarity_scores = []

            for embedding, filename in zip(other_embeddings, other_filenames):
                similarity_score = 1 - cosine(reference_embedding, embedding)
                similarity_scores.append((filename, similarity_score))

            # Sort similarity scores in descending order
            sorted_similarity_scores = sorted(similarity_scores, key=lambda x: x[1], reverse=True)

            # Filter similarity scores based on the slider value
            filtered_similarity_scores = [score for score in sorted_similarity_scores if score[1] >= similarity_threshold]

            if filtered_similarity_scores:
                # Display the reference image
                st.subheader("Reference Image")
                st.image(reference_image, use_column_width=True)

                # Display the images based on similarity scores in a 4-column matrix layout
                st.subheader("Similar Images")
                num_columns = 4
                num_images = len(filtered_similarity_scores)
                num_rows = (num_images + num_columns - 1) // num_columns

                for row in range(num_rows):
                    columns = st.columns(num_columns)
                    for col in range(num_columns):
                        index = row * num_columns + col
                        if index < num_images:
                            filename, score = filtered_similarity_scores[index]
                            image_path = os.path.join(image_directory, filename)
                            image = Image.open(image_path)
                            with columns[col]:
                                st.image(image, caption=f"{filename} (Similarity Score: {score:.2f})", use_column_width=True)

                # Create a list to store image data
                image_data = []

                # Iterate over filtered similarity scores
                for filename, score in filtered_similarity_scores:
                    image_path = os.path.join(image_directory, filename)
                    image = Image.open(image_path)
                    image_thumbnail = image.copy()
                    image_thumbnail.thumbnail((100, 100))

                    # Convert image_thumbnail to RGB
                    image_thumbnail = image_thumbnail.convert("RGB")

                    # Convert image to bytes
                    img_bytes = BytesIO()
                    image_thumbnail.save(img_bytes, format='PNG')
                    img_bytes = img_bytes.getvalue()

                    # Encode the image to base64
                    encoded_image = base64.b64encode(img_bytes).decode()

                    # Append the image data to the list
                    image_data.append(encoded_image)

                # Prepare data for plotting
                filenames = [filename for filename, _ in filtered_similarity_scores]
                scores = [score for _, score in filtered_similarity_scores]

                # Create a figure
                fig = go.Figure()

                # Add trace for similarity scores
                fig.add_trace(go.Bar(
                    y=filenames,
                    x=scores,
                    orientation='h',
                    marker=dict(
                        color=scores,
                        colorscale='Viridis',
                        reversescale=True
                    ),
                    text=[f"{score:.2f}" for score in scores],
                    textposition='inside',
                    textfont=dict(color='white', size=12),
                    hoverinfo='none'
                ))

                # Add images to the chart
                for i, (encoded_image, score) in enumerate(zip(image_data, scores)):
                    fig.add_layout_image(
                        dict(
                            source=f"data:image/png;base64,{encoded_image}",
                            xref="x",
                            yref="y",
                            x=score + 0.05,
                            y=i,
                            sizex=0.1,
                            sizey=0.8,
                            xanchor="left",
                            yanchor="middle",
                            layer="above"
                        )
                    )

                # Update the layout
                fig.update_layout(
                    title=dict(
                        text="Similarity Scores",
                        x=0.05,
                        y=0.95,
                        xanchor="left",
                        yanchor="top"
                    ),
                    xaxis=dict(title="Similarity Score", range=[0.1, 1]),
                    yaxis=dict(title="Image", autorange="reversed"),
                    height=1000,
                    width=None,
                    template="plotly_white",
                    hovermode='closest',
                    dragmode='pan'
                )

                # Display the chart in Streamlit
                st.subheader("Similarity Score Chart")
                st.plotly_chart(fig, use_container_width=True)

            else:
                st.warning("There are no similar images above the specified threshold.")

        except KeyError as e:
            st.error(f"Error: Missing Key in API response - {str(e)}")
    else:
        st.error(f"Error: API request failed with status code {response.status_code}")
        st.error(f"Response Content: {response.text}")