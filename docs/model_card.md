# Model Card

## Model Overview

The project uses two pre-trained OpenCV Zoo models:

- YuNet for face detection.
- SFace for face recognition embeddings.

They are used through OpenCV DNN APIs:

- `cv2.FaceDetectorYN_create`
- `cv2.FaceRecognizerSF_create`

## Intended Use

The models are used inside an academic computer vision prototype that compares the largest detected face in a selfie-with-document image with smaller candidate faces detected on the document.

The output is a similarity score and a threshold-based match/no-match decision for experimentation.

## Out-of-Scope Use

The system must not be used for:

- legal identity verification;
- production onboarding;
- surveillance;
- access control;
- fraud decisions;
- any automated decision that can affect a real person.

## Custom Logic Added by This Project

The pre-trained models are combined with project-specific logic:

- single-image assumption;
- largest-face selection as the live face;
- smaller faces as document candidates;
- best-candidate selection;
- threshold decision;
- annotated result preview;
- classical fallback with Haar, LBP, and gradient histograms;
- evaluation and threshold tuning scripts.

## Limitations

Performance can degrade when:

- the document portrait is too small;
- glare or blur affects the document;
- the live face is partially occluded;
- the image contains unrelated faces;
- the largest detected face is not the live user;
- synthetic data differs from real camera images.

## Bias and Fairness

Face recognition systems may perform differently across demographic groups, lighting conditions, camera quality, age, pose, and image compression. This project does not claim fairness or demographic robustness without an explicit evaluation dataset designed for that purpose.

## Data Handling

The app deletes uploaded images after processing and does not store biometric embeddings.
