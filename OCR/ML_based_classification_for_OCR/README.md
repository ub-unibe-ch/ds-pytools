# Tools for machine learning based classification in the context of OCR

### character_classification  
The automatic classification of images displaying characters 
is the core element of optical character recognition (OCR).
This Jupyter notebook presents a machine learning based approach
suitable for OCR with printed digits.  

The folder *predict_img* contains images of individual digits required for label prediction. The images were obtained by table and data field segmentation of weather tables published in the *Bozner Wochenblatt* (later called *Bozner Zeitung*) (Source: [Landesbibliothek Dr. Friedrich Teßmann](https://digital.tessmann.it), License: [CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/)).  
The file *digits_0-9.csv* contains the pixel data of individual digit images and labels used as training data for a machine learning algorithm. The images were obtained as described above, using the same source (same licence).  
The file *cc_trained_algorithm.joblib* provides the trained machine learning model.
