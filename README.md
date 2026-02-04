# AI Capstone Project - TTC Delay Prediction

**Course:** AI Capstone Project - COMP385402.12558.2026W  
**Professor:** Hakim Klif  
**Institution:** Centennial College

## Project Overview

This project aims to develop an **AI-based SaaS solution** for predicting delays in Toronto's public transportation system (TTC - Toronto Transit Commission). The system will predict delays for buses, subways, and streetcars using historical delay data and machine learning models.

## Group Members

The project team consists of the following students (sorted alphabetically by name):

1. **Absar Siddiqui-Atta**
2. **Bruna De Fatima Miranda Figueiredo Cruz**
3. **Felipe Rosa**
4. **Krishan Singh**
5. **Marco Favaretto**

## Project Structure

```
centennialCollege_AICapstoneProject/
├── aiProject/                    # Main AI/ML project code
│   ├── 01_EDA_TTC_Delay_Prediction.ipynb  # Exploratory Data Analysis & Data Processing
│   ├── outputs/                  # Processed datasets and model outputs
│   └── requirements.txt          # Python dependencies
├── brainstorming/                # Initial data gathering and exploration scripts
│   ├── download_ttc_*.py        # Data download scripts
│   └── unify_ttc_datasets.py    # Dataset unification script
├── dataset/                      # Raw and processed datasets
│   ├── ttc-bus-delay-data/      # Bus delay data (2017-2025)
│   ├── ttc-streetcar-delay-data/ # Streetcar delay data (2017-2025)
│   ├── ttc-subway-delay-data/   # Subway delay data (2017-2025)
│   └── ttc-lrt-delay-data/      # LRT delay data
└── README.md                     # This file
```

## Dataset

The project uses TTC delay data from **2017 to 2025**, covering:
- **Bus delays**: ~263,712 records
- **Subway delays**: ~108,913 records
- **Streetcar delays**: ~67,030 records

**Total:** ~439,655 delay records

Data sources:
- Toronto Open Data Portal: https://open.toronto.ca/
- Datasets include: Date, Time, Line/Route, Station, Delay Code, Delay Duration, Gap Duration, Vehicle ID, Direction/Bound

## Getting Started

### Prerequisites

- Python 3.8+
- Jupyter Notebook
- Virtual environment (recommended)

### Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd centennialCollege_AICapstoneProject
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   cd aiProject
   pip install -r requirements.txt
   ```

4. **Run the EDA notebook:**
   ```bash
   jupyter notebook 01_EDA_TTC_Delay_Prediction.ipynb
   ```

## Current Status

### Completed ✅

- **Data Collection**: Downloaded raw TTC delay datasets (2017-2025)
- **Data Unification**: Merged bus, subway, and streetcar datasets into unified format
- **Exploratory Data Analysis**: Comprehensive EDA with visualizations
- **Data Processing**:
  - Missing value handling
  - Feature engineering (temporal, cyclical, binary flags)
  - Normalization and transformations
  - Target variable definition
- **Processed Dataset**: Saved processed dataset ready for modeling

### In Progress / Next Steps ⚠️

- Model development and training
- Model evaluation and optimization
- SaaS application development
- Deployment and testing

## Key Features

- **Multi-modal prediction**: Handles bus, subway, and streetcar delays
- **Temporal analysis**: Time-based features (hour, day, season, rush hours)
- **Feature engineering**: Cyclical encodings, binary flags, delay ratios
- **Data quality**: Comprehensive missing value handling and normalization

## Technologies

- **Python**: Data processing and analysis
- **Pandas**: Data manipulation
- **NumPy**: Numerical computations
- **Matplotlib/Seaborn**: Data visualization
- **Scikit-learn**: Machine learning preprocessing
- **Jupyter Notebooks**: Interactive development

## License

This project is part of an academic capstone project at Centennial College.

## Contact

For questions or contributions, please contact the project team members listed above.

---

**Last Updated:** January 2025
