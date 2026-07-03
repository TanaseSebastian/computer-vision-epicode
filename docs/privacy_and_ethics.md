# Privacy and Ethics

## Data Handling

The app receives a single selfie-with-document image for verification. Uploaded images are saved only as temporary files in `app/uploads/` and deleted immediately after each request finishes.

The project should not store:

- identity documents;
- selfies;
- biometric embeddings;
- names, document numbers, addresses, or other personally identifiable information.

## Security Notes

- Only image extensions `jpg`, `jpeg`, `png`, and `webp` are accepted.
- Flask limits upload size to 8 MB.
- Filenames are sanitized with Werkzeug `secure_filename`.
- The project is a local academic prototype and should not be exposed publicly without authentication, HTTPS, logging review, rate limiting, and stronger storage controls.

## Bias and Limitations

Face verification systems can perform differently across camera quality, lighting, skin tone, age, pose, occlusions, image compression, and document type. Synthetic datasets may not represent real-world variation.

The model output is a similarity score, not proof of identity. Decisions should be presented as experimental results only.

## Ethical Use

This project is intended for computer vision education. It should not be used for real identity checks, access control, surveillance, fraud decisions, legal verification, or any context where a false match or false rejection could harm a person.
