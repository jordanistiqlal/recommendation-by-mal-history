import pandas as pd
import gc
from app.services.dataset_store import get_dataset, parse_list

def analysis_anime(data):
    df = pd.DataFrame(data)
    df.rename(columns={'id': 'mal_id'}, inplace=True)
    df.rename(columns={'score': 'my_score'}, inplace=True)

    if len(data) < 1:
        return {"genre": [],"studio": [],"producer": [],"demographic": [],"theme": [],"anime_time": [],"recommendation": []}

    dataset = get_dataset()

    df['mal_id'] = pd.to_numeric(df['mal_id'], errors='coerce')

    cols_to_drop = [col for col in df.columns if col in dataset.columns and col != 'mal_id']
    df_clean = dataset.drop(columns=cols_to_drop+['image_url'])

    merged_df = pd.merge(df, df_clean, on='mal_id', how='inner')
    merged_df = merged_df.drop(['Unnamed: 0'], axis=1)

    analysis_df = merged_df.copy()

    genre = fetch_genre(analysis_df)
    studio = fetch_studio(analysis_df)
    producer = fetch_producer(analysis_df)
    demographic = fetch_demographic(analysis_df)
    theme = fetch_theme(analysis_df)
    anime_time = fetch_anime_time(analysis_df)
    analysis = fetch_analysis(analysis_df)

    result = {
        "genre": genre,
        "studio": studio,
        "producer": producer,
        "demographic": demographic,
        "theme": theme,
        "anime_time": anime_time,
        "recommendation": analysis
    }

    del df, df_clean, merged_df, analysis_df, dataset
    gc.collect()

    return result

def fetch_studio(df):
    temp_df = df[['studio']].copy()
    temp_df['studio'] = temp_df['studio'].apply(parse_list)

    studio_df = temp_df.explode('studio')['studio'].value_counts().reset_index()
    studio_df.columns = ['studios', 'count']

    result = studio_df.to_dict(orient='records')

    del temp_df, studio_df
    gc.collect()

    return result

def fetch_genre(df):
    temp_df = df[['genre']].copy()
    temp_df['genre'] = temp_df['genre'].apply(parse_list)

    genre_df = temp_df.explode('genre')['genre'].value_counts().reset_index()
    genre_df.columns = ['genres', 'count']

    result = genre_df.to_dict(orient='records')

    del temp_df, genre_df
    gc.collect()

    return result

def fetch_producer(df):
    temp_df = df[['producer']].copy()
    temp_df['producer'] = temp_df['producer'].apply(parse_list)

    producer_df = temp_df.explode('producer')['producer'].value_counts().reset_index()
    producer_df.columns = ['producers', 'count']

    result = producer_df.to_dict(orient='records')

    del temp_df, producer_df
    gc.collect()

    return result

def fetch_demographic(df):
    required_demographics = ['Shounen', 'Seinen', 'Shoujo', 'Josei', 'Kids']
    temp_df = df[['demographic']].copy()
    
    if temp_df['demographic'].dtype == 'object':
        temp_df['demographic'] = temp_df['demographic'].apply(parse_list)
    
    demographic_series = temp_df.explode('demographic')['demographic']
    demographic_df = (
        demographic_series.value_counts()
        .reindex(required_demographics, fill_value=0)
        .reset_index()
    )
    demographic_df.columns = ['demographics', 'count']
    
    result = demographic_df.to_dict(orient='records')
    
    del temp_df, demographic_series, demographic_df
    gc.collect()
    
    return result

def fetch_theme(df):
    temp_df = df[['theme']].copy()
    temp_df['theme'] = temp_df['theme'].apply(parse_list)

    theme_df = temp_df.explode('theme')['theme'].value_counts().reset_index()
    theme_df.columns = ['themes', 'count']
    theme_df = theme_df[theme_df['themes'] != '-']

    result = theme_df.to_dict(orient='records')
    
    del temp_df, theme_df
    gc.collect()
    
    return result

def fetch_anime_time(df):
    temp_df = df[['premiered']].copy()
    temp_df['premiered'] = temp_df['premiered'].str.replace('  ', ' ', regex=False).str.strip()
    temp_df = temp_df[~temp_df['premiered'].isin(['-', '?'])]
    
    temp_df['season'] = temp_df['premiered'].str.extract(r'^(Fall|Spring|Summer|Winter)', expand=False)
    temp_df['year'] = temp_df['premiered'].str.extract(r'(\d{4})', expand=False)
    
    temp_df = temp_df.dropna(subset=['season', 'year'])
    count_df = temp_df.groupby(['year', 'season']).size().reset_index(name='count')
    
    season_order = ['Fall', 'Spring', 'Summer', 'Winter']
    full_index = pd.MultiIndex.from_product(
        [count_df['year'].unique(), season_order],
        names=['year', 'season']
    )
    
    final_df = (
        count_df.set_index(['year', 'season'])
        .reindex(full_index, fill_value=0)
        .reset_index()
    )
    
    final_df['time'] = final_df['season'] + ' ' + final_df['year']
    final_df['season'] = pd.Categorical(
        final_df['season'],
        categories=season_order,
        ordered=True
    )
    
    final_df = final_df.sort_values(['year', 'season'])
    time_df = final_df[['time', 'count']].reset_index(drop=True)
    
    result = time_df.to_dict(orient='records')
    
    del temp_df, count_df, final_df, time_df
    gc.collect()
    
    return result

def fetch_analysis(df):
    return []

def main():
    while True:
        analysis_anime()

if __name__ == "__main__":
    main()