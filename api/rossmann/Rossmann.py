import pickle as pkl
import pandas as pd
import numpy as np
import datetime

class Rossmann( object ):
    def __init__(self):
        # It's assumed these scalers were fit and saved during the notebook phase.
        # The file names are inferred from the notebook logic.
        path = '../model/'
        self.competition_distance_scaler = pkl.load(open(path + 'pre-processing/robust_scaler_competition_distance.pkl', 'rb'))
        self.competition_time_month_scaler = pkl.load(open(path + 'pre-processing/robust_scaler_competition_time_month.pkl', 'rb'))
        self.promo_time_week_scaler = pkl.load(open(path + 'pre-processing/minmax_scaler_promo_time_week.pkl', 'rb'))
        self.year_scaler = pkl.load(open(path + 'pre-processing/minmax_scaler_year.pkl', 'rb'))
        self.store_type_encoder = pkl.load(open(path + 'pre-processing/label_encoder_store_type.pkl', 'rb'))
        self.features_selected = pkl.load(open(path + 'pre-processing/list_features_selected.pkl', 'rb'))
        
        # Load the trained model
        self.model = pkl.load(open(path + 'modeling/c01_xgb_final.pkl', 'rb'))

    def preprocess(self, data):
        """Applies the full preprocessing pipeline."""
        df = self._data_cleaning(data.copy())
        df = self._feature_engineering(df)
        df = self._data_preparation(df)
        
        # Ensure only selected features are returned
        features_for_model = [col for col in self.features_selected if col not in ['Date', 'Sales']]
        return df[features_for_model]

    def _data_cleaning(self, df):
        # Filter out closed stores, as they are not relevant for sales prediction.
        # The filter for Sales > 0 is only applied during the training phase.
        df = df[df['Open'] == 1].copy()

        # Convert Date to datetime
        df['Date'] = pd.to_datetime(df['Date'])

        # Impute missing values using vectorized operations
        df['CompetitionDistance'] = df['CompetitionDistance'].fillna(200000.0)
        df['CompetitionOpenSinceMonth'] = df['CompetitionOpenSinceMonth'].fillna(df['Date'].dt.month)
        df['CompetitionOpenSinceYear'] = df['CompetitionOpenSinceYear'].fillna(df['Date'].dt.year)
        df['Promo2SinceWeek'] = df['Promo2SinceWeek'].fillna(df['Date'].dt.isocalendar().week)
        df['Promo2SinceYear'] = df['Promo2SinceYear'].fillna(df['Date'].dt.year)
        df['PromoInterval'] = df['PromoInterval'].fillna('none')

        # Convert types after imputation
        df['CompetitionOpenSinceMonth'] = df['CompetitionOpenSinceMonth'].astype(int)
        df['CompetitionOpenSinceYear'] = df['CompetitionOpenSinceYear'].astype(int)
        df['Promo2SinceWeek'] = df['Promo2SinceWeek'].astype(int)
        df['Promo2SinceYear'] = df['Promo2SinceYear'].astype(int)
        
        return df

    def _feature_engineering(self, df):
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
        # Rescaling
        df['CompetitionDistance'] = self.competition_distance_scaler.transform(df[['CompetitionDistance']].values)
        df['CompetitionTimeMonth'] = self.competition_time_month_scaler.transform(df[['CompetitionTimeMonth']].values)
        df['PromoTimeWeek'] = self.promo_time_week_scaler.transform(df[['PromoTimeWeek']].values)
        df['Year'] = self.year_scaler.transform(df[['Year']].values)

        # Encoding
        df['StateHoliday'] = df['StateHoliday'].replace({'a': 'public', 'b': 'easter', 'c': 'christmas', '0': 'none'})
        df = pd.get_dummies(df, prefix=['StateHoliday'], columns=['StateHoliday'])

        df['StoreType'] = self.store_type_encoder.transform(df['StoreType'])

        assortment_dict = {'basic': 1, 'extra': 2, 'extended': 3}
        df['Assortment'] = df['Assortment'].replace({'a': 'basic', 'b': 'extra', 'c': 'extended'}).map(assortment_dict)

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

    def get_prediction( self, original_data, test_data ):
        # Fazer a previsão com os dados preparados
        pred = self.model.predict( test_data )

        # Filtrar os dados originais para incluir apenas as lojas que estavam abertas,
        # garantindo que o comprimento corresponda ao das previsões.
        data_to_predict = original_data[original_data['Open'] == 1].copy()

        # Adicionar a coluna de previsão aos dados filtrados
        data_to_predict['Prediction'] = np.expm1( pred )
        return data_to_predict.to_json( orient='records', date_format='iso' )
        