import pandas as pd
import numpy as np
import logging

# Configure logging for the module
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class Rossmann:
    def __init__(self, model, scalers, encoders, features_selected):
        """
        Initializes the Rossmann object with preloaded model and preprocessing objects.

        Parameters
        ----------
        model : object
            The trained model for sales prediction.
        scalers : dict
            Dictionary with scaler objects for each feature (competition_distance, competition_time_month, promo_time_week, year).
        encoders : dict
            Dictionary with encoder objects for each categorical feature (store_type).
        features_selected : list
            List of features selected for the model.

        Returns
        -------
        None
        """
        self.model = model
        self.features_selected = features_selected

        # Scalers
        self.competition_distance_scaler = scalers["competition_distance_scaler"]
        self.competition_time_month_scaler = scalers["competition_time_month_scaler"]
        self.promo_time_week_scaler = scalers["promo_time_week_scaler"]
        self.year_scaler = scalers["year_scaler"]

        # Encoders
        self.store_type_encoder = encoders["store_type_encoder"]

        logging.info("Rossmann initialized with preloaded objects.")

    def preprocess(self, df):
        """
        Preprocesses the input DataFrame by performing data cleaning, feature engineering, and data preparation.

        Parameters
        ----------
        df : pandas.DataFrame
            The input DataFrame containing the raw data to be preprocessed.

        Returns
        -------
        pandas.DataFrame
            A DataFrame with selected features ready for model prediction.
        """
        df = self._data_cleaning(df.copy())
        df = self._feature_engineering(df)
        df = self._data_preparation(df)

        features_for_model = [col for col in self.features_selected if col not in ["Date", "Sales"]]
        return df[features_for_model]

    def _data_cleaning(self, df):
        """
        Performs data cleaning, including type conversion, missing value imputation, and category renaming.

        Parameters
        ----------
        df : pandas.DataFrame
            The DataFrame containing the raw data to be cleaned.

        Returns
        -------
        pandas.DataFrame
            The DataFrame with cleaned data, ready for feature engineering.
        """
        # Filter out closed stores, as they are not relevant for sales prediction.
        # The filter for Sales > 0 is only applied during the training phase.
        df = df[df['Open'] == 1].copy()
        
        # Convert Date to datetime
        df['Date'] = pd.to_datetime(df.Date, format='%Y-%m-%d')

        # -- Impute missing values using vectorized operations --
        df['Date'] = pd.to_datetime(df.Date, format='%Y-%m-%d')
        df['CompetitionDistance'] = df['CompetitionDistance'].fillna(200000.0)
        df['CompetitionOpenSinceYear'] = df['CompetitionOpenSinceYear'].fillna(df['Date'].dt.year)
        df['CompetitionOpenSinceMonth'] = df['CompetitionOpenSinceMonth'].fillna(df['Date'].dt.month)
        df['Promo2SinceWeek'] = df['Promo2SinceWeek'].fillna(df['Date'].dt.isocalendar().week)
        df['Promo2SinceYear'] = df['Promo2SinceYear'].fillna(df['Date'].dt.year)
        df['PromoInterval'] = df['PromoInterval'].fillna('none')

        # -- Convert types after imputation --
        df['CompetitionOpenSinceMonth'] = df['CompetitionOpenSinceMonth'].astype(int)
        df['CompetitionOpenSinceYear'] = df['CompetitionOpenSinceYear'].astype(int)
        df['Promo2SinceWeek'] = df['Promo2SinceWeek'].astype(int)
        df['Promo2SinceYear'] = df['Promo2SinceYear'].astype(int)
        df['CompetitionDistance'] = df['CompetitionDistance'].astype(int)

        # Categorical values
        df['PromoInterval'] = df['PromoInterval'].astype('category')
        df['StateHoliday'] = df['StateHoliday'].astype('category')
        df['StoreType'] = df['StoreType'].astype('category')
        df['Assortment'] = df['Assortment'].astype('category')

        # Boolean values
        df['Promo'] = df['Promo'].astype('bool')
        df['Promo2'] = df['Promo2'].astype('bool')
        df['SchoolHoliday'] = df['SchoolHoliday'].astype('bool')

        # -- Change category values --
        # StateHoliday
        # a = public holiday
        # b = Easter holiday
        # c = Christmas
        # 0 = None
        df['StateHoliday'] = df['StateHoliday'].cat.rename_categories({
            'a':'public', 
            'b':'easter',
            'c':'christmas',
            '0':'none'})

        # Assortment
        # a = basic
        # b = extra
        # c = extended
        df['Assortment'] = df['Assortment'].cat.rename_categories({
            'a':'basic',
            'b':'extra',
            'c':'extended'
        })
        df['Assortment'] = pd.Categorical(
            df['Assortment'],
            categories=[
                'basic', 
                'extra', 
                'extended'
            ],
            ordered=True
        )
        return df

    def _feature_engineering(self, df):
        """
        Creates new features from the existing ones in the input DataFrame.

        Parameters
        ----------
        df : pandas.DataFrame
            The input DataFrame containing the raw data to be processed.

        Returns
        -------
        pandas.DataFrame
            A DataFrame with the new features created during feature engineering.
        """
        # Date-based features
        df['Year'] = df['Date'].dt.year
        df['Month'] = df['Date'].dt.month
        df['Day'] = df['Date'].dt.day
        df['WeekOfYear'] = df['Date'].dt.isocalendar().week.astype(int)

        # Competition related features
        df['CompetitionSince'] = pd.to_datetime(df['CompetitionOpenSinceYear'].astype(str) + '-' + df['CompetitionOpenSinceMonth'].astype(str) + '-01')
        df['CompetitionTimeMonth'] = ((df['Date'] - df['CompetitionSince']).dt.days / 30).astype(int)

        # Promotion related features
        df['PromoSince'] = df['Promo2SinceYear'].astype(str) + '-' + df['Promo2SinceWeek'].astype(str)
        df['PromoSince'] = pd.to_datetime(df['PromoSince'] + '-1', format='%Y-%W-%w') - pd.to_timedelta(7, unit='d')
        df['PromoTimeWeek'] = ((df['Date'] - df['PromoSince']) / np.timedelta64(1, 'W')).astype(int)

        # IsPromo feature
        month_map = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}
        df['MonthMap'] = df['Date'].dt.month.map(month_map)
        df['IsPromo'] = df.apply(lambda x: 1 if x['PromoInterval'] != 'none' and x['MonthMap'] in x['PromoInterval'] else 0, axis=1)

        # Drop auxiliary columns
        df.drop(columns=['MonthMap', 'PromoInterval', 'CompetitionSince', 'PromoSince'], inplace=True)

        return df

    def _data_preparation(self, df):
        """
        Performs data preparation, including normalization, encoding, and cyclical feature transformation.

        Parameters
        ----------
        df : pandas.DataFrame
            The DataFrame containing the raw data to be prepared.

        Returns
        -------
        pandas.DataFrame
            The DataFrame with prepared data, ready for model training.
        """
        # Rescaling
        df['CompetitionDistance'] = self.competition_distance_scaler.transform(df[['CompetitionDistance']].values)
        df['CompetitionTimeMonth'] = self.competition_time_month_scaler.transform(df[['CompetitionTimeMonth']].values)
        df['PromoTimeWeek'] = self.promo_time_week_scaler.transform(df[['PromoTimeWeek']].values)
        df['Year'] = self.year_scaler.transform(df[['Year']].values)
        df['Promo2SinceYear'] = self.year_scaler.transform(df[['Promo2SinceYear']].values)
        df['CompetitionOpenSinceYear'] = self.year_scaler.transform(df[['CompetitionOpenSinceYear']].values)
        
        # Encoding
        df = pd.get_dummies(df, prefix=['StateHoliday'], columns=['StateHoliday'] )

        df['StoreType'] = self.store_type_encoder.transform(df['StoreType'])

        assortmentDict = {'basic': 1,  'extra': 2, 'extended': 3}
        df['Assortment'] = df['Assortment'].map(assortmentDict)
        df['Assortment'] = df['Assortment'].astype(int)

        # Cyclical Feature Transformation
        pi = np.pi
        df['DayOfWeekSin'] = np.sin(df['DayOfWeek'] * (2. * pi / 7))
        df['DayOfWeekCos'] = np.cos(df['DayOfWeek'] * (2. * pi / 7))
        df['MonthSin'] = np.sin(df['Month'] * (2. * pi / 12))
        df['MonthCos'] = np.cos(df['Month'] * (2. * pi / 12))
        df['DaySin'] = np.sin(df['Day'] * (2. * pi / 30))
        df['DayCos'] = np.cos(df['Day'] * (2. * pi / 30))
        df['WeekOfYearSin'] = np.sin(df['WeekOfYear'] * (2. * pi / 52))
        df['WeekOfYearCos'] = np.cos(df['WeekOfYear'] * (2. * pi / 52))

        return df

    def get_prediction(self, test_data):
        """
        Requests a prediction from the model with the processed input data.

        Parameters
        ----------
        test_data : pandas.DataFrame
            The DataFrame containing the processed input data for prediction.

        Returns
        -------
        str
            The prediction result in JSON format with columns "Store", "DayOfWeek", "Date", "Sales", and "Prediction".
        """
        # Model prediction and post-processing
        pred = self.model.predict(test_data)
        test_data["Prediction"] = np.expm1(pred)
        return test_data.to_json(orient="records", date_format="iso")