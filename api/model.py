import torch
from torchvision import transforms
from torchvision.models import resnet50, ResNet50_Weights


# Check available models
'''vision_models = dir(torchvision.models)
for model in vision_models:
    print(model)'''

# Load a pre-trained mdoel from PyTorch
model = resnet50(weights=None)
state_dict = torch.load('./resnet50-11ad3fa6.pth')
model.load_state_dict(state_dict)
model.eval()

# Define preprocessing transforms
# Check PyTorch Documentation, values differ for different pre-trained models
preprocess = transforms.Compose([
    transforms.Resize(232),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean = [0.485, 0.456, 0.406], std = [0.229, 0.224, 0.225])
])

def generate_embeddings(images):
    embeddings = []
    for image in images:
        # preprocess image
        preprocessed_image = preprocess(image)
        preprocessed_image = preprocessed_image.unsqueeze(0)

        # Generate Embeddings
        with torch.no_grad():
            embedding = model(preprocessed_image)
            embedding = embedding.squeeze().cpu().numpy()
        embeddings.append(embedding)
    return embeddings
