"""
This program creates a set of scores from O*NET 
data about the ways that employees rate the tasks
they do in their job. The idea is that each of the
three metrics (frequency of task, importance of task,
relevance of task to the job) can be standardised, weighted,
and combined to form an overall value of a task's centrality
to each job title.

Current averages of each metric after finding proportions:
Frequency: 0.21380864875917643
Importance: 0.7218961413905746
Relevance: 0.7659782634216267

The program currently weights all three metrics evenly (1)
"""

import pandas as pd

# weighting different factors evenly for now.
IMPORTANCE_WEIGHT = 1
RELEVANCE_WEIGHT = 1
FREQUENCY_WEIGHT = 1

def pivot_data():
    """
    Takes the O*NET data and creates a flat table so that
    each Scale Name / Category combination (rating) has a column
    """

    task_ratings_data = pd.read_excel('data/Task Ratings.xlsx')

    # Temporarily fill NaN values in 'Category' with a placeholder
    task_ratings_data['Category'] = task_ratings_data['Category'].fillna('NoCategory')

    # Pivoting the table
    pivoted_df = task_ratings_data.pivot_table(
        index=['O*NET-SOC Code', 'Title', 'Task ID', 'Task'],
        columns=['Scale Name', 'Category'],
        values='Data Value',
        aggfunc='first'
    ).reset_index()

    # Flattening the MultiIndex columns
    pivoted_df.columns = [' '.join(str(col).split()).strip() for col in pivoted_df.columns.values]


    # Resetting the index
    pivoted_df.reset_index(drop=True, inplace=True)

    pivoted_df.rename(
        columns={
            "('Frequency of Task (Categories 1-7)', 1.0)": 'Frequency_1',
            "('Frequency of Task (Categories 1-7)', 2.0)": 'Frequency_2',
            "('Frequency of Task (Categories 1-7)', 3.0)": 'Frequency_3',
            "('Frequency of Task (Categories 1-7)', 4.0)": 'Frequency_4',
            "('Frequency of Task (Categories 1-7)', 5.0)": 'Frequency_5',
            "('Frequency of Task (Categories 1-7)', 6.0)": 'Frequency_6',
            "('Frequency of Task (Categories 1-7)', 7.0)": 'Frequency_7',
            "('Importance', 'NoCategory')": "Importance",
            "('Relevance of Task', 'NoCategory')": "Relevance"
        },
        inplace=True
    )
    pivoted_df.to_csv("outputs/pivoted_df.csv")
    return pivoted_df

def normalise_data(data):
    """
    Apply min-max scaling to rating values.
    """
    for col in data.columns:
        if 'Importance' in col or 'Relevance' in col:
            data[col] = min_max(data, col)

    # multiplying each percentage of respondents by a weight corresponding
    # to frequency with respect to days. i.e., 1 is equivalent to once per day
    data['Frequency_1'] = data['Frequency_1'] * 1/220
    data['Frequency_2'] = data['Frequency_2'] * 6/220
    data['Frequency_3'] = data['Frequency_3'] * 1/12
    data['Frequency_4'] = data['Frequency_4'] * 1/7
    data['Frequency_5'] = data['Frequency_5'] * 1
    data['Frequency_6'] = data['Frequency_6'] * 4
    data['Frequency_7'] = data['Frequency_7'] * 8

    data['Average Frequency'] = (
        data['Frequency_1'] +
        data['Frequency_2'] +
        data['Frequency_3'] +
        data['Frequency_4'] +
        data['Frequency_5'] +
        data['Frequency_6'] +
        data['Frequency_7']
    )
    # print("---- Min and max of average freq BEFORE normlisation ----")
    # print(data['Average Frequency'].min())
    # print(data['Average Frequency'].max())

    data['Average Frequency'] = min_max(data, 'Average Frequency')
    # print("---- average of average freq AFTER normlisation ----")
    # print(data['Average Frequency'].mean())

    data.to_csv("outputs/normalised_df.csv")

    # print("---- average of importance AFTER normlisation ----")
    # print(data['Importance'].mean())

    # print("---- average of relevance freq AFTER normlisation ----")
    # print(data['Relevance'].mean())
    return data

def min_max(data, col):
    """
    helper to do min max calc for normalisation.
    """
    max_val = data[col].max()
    min_val = data[col].min()
    data[col] = (data[col] - min_val) / (max_val - min_val)
    return data[col]

def find_proportions(data):
    """
    Calculates a weighted value for each task's importance.
    """
    # create a new dataframe for the extra
    # weight and proportion cols.
    headers = data.columns.tolist() + [
        'Total Importance',
        'Importance Proportion',
        'Freq Score Total',
        'Frequency Proportion',
        'Total Relevance',
        'Relevance Proportion',
        'Unweighted Sum',
        'Sum Proportion',
        'Weighted Sum',
        'Weighted Sum Proportion'
    ]
    pd.DataFrame(columns=headers).to_csv(
        'outputs/weighted_proportions.csv', 
        index=False
    )
    unique_occupations = data["('O*NET-SOC Code', '')"].unique()

    # calculate the weights and proportions for each job title in turn.
    for occupation in unique_occupations:
        occupation_data = data[
            data["('O*NET-SOC Code', '')"] == occupation
        ].copy()

        # proportion of each task's importance score
        occupation_data['Total Importance'] = occupation_data['Importance'].sum()
        occupation_data['Importance Proportion'] = (
            occupation_data['Importance']
        ) / (
            occupation_data['Total Importance']
        )

        # proportion of each task's frequency score
        occupation_data['Freq Score Total'] = occupation_data['Average Frequency'].sum()
        occupation_data['Frequency Proportion'] = (
            occupation_data['Average Frequency']
        ) / (
            occupation_data['Freq Score Total']
        )

        # proportion of each task's relevance score
        occupation_data['Total Relevance'] = occupation_data['Relevance'].sum()
        occupation_data['Relevance Proportion'] = (
            occupation_data['Relevance']
        ) / (
            occupation_data['Total Relevance']
        )

        # Find the the total unweighted score for each task
        occupation_data['Unweighted Sum'] = (
            occupation_data['Importance Proportion'] +
            occupation_data['Frequency Proportion'] +
            occupation_data['Relevance Proportion']
        )

        # calculate the unweighted proportion of the score for
        # each task with respect to the job title
        total_sum = occupation_data['Unweighted Sum'].sum()
        occupation_data['Sum Proportion']  = (
            occupation_data['Unweighted Sum']
        ) / total_sum

        # Calculate the weighted sum of the proportions
        occupation_data['Weighted Sum'] = (
            occupation_data['Importance Proportion'] * IMPORTANCE_WEIGHT
        ) + (
            occupation_data['Frequency Proportion'] * FREQUENCY_WEIGHT
        ) + (
            occupation_data['Relevance Proportion'] * RELEVANCE_WEIGHT
        )

        # Calculate the proportion of the weighted sum for each task
        # compared to the total weighted sum for the occupation
        total_weighted_sum = occupation_data['Weighted Sum'].sum()
        occupation_data['Weighted Sum Proportion'] = (
            occupation_data['Weighted Sum']
        ) / total_weighted_sum

        # Append processed data for this occupation to the output CSV
        occupation_data.to_csv(
            'outputs/weighted_proportions.csv',
            mode='a',
            header=False,
            index=False
        )

DATA = pivot_data()
DATA = normalise_data(DATA)
find_proportions(DATA)

# data = pd.read_csv('outputs/weighted_proportions.csv')
# print("Importance prop: ",data['Importance Proportion'].mean())
# print("Relevance prop: ", data['Relevance Proportion'].mean())
# print("Frequency prop: ", data['Frequency Proportion'].mean())
