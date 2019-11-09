import pandas as pd
import matplotlib.pyplot as plt 
import seaborn as sns
import os

pd.set_option('display.expand_frame_repr', False)

# Cleaning

''''
Clean up the CSV and organize it into a data frame
'''

# Read in the file
file = pd.read_csv("teaching_data_1.csv")

# Strip the extra text that got scraped up with the name box
    # maybe fix this in the scraper
for i in range(len(file)):

    
    word_list = ["See Corrections", "See Lesson Info", "Add Student to my Regulars"]
    for word in word_list:
        if word in file.Name[i]:
            file.Name[i] = file.Name[i].replace(word, "")
    file.Name[i] = file.Name[i].strip()

# Convert Date column to datetime object (inferring format)
# file['Date'] = pd.to_datetime(format = %m %d, %y %I:%M %p)
file['Date'] = pd.to_datetime(file['Date'], infer_datetime_format = True)

# no need to separate time into different column, as stats can just be filtered by either date or time
# convert the string in the length column to int (minutes)
for i in range(len(file)):
    file.loc[i, 'Length'] = int(file.Length[i][:2])

# Rename "Length" to "Duration"
file.rename(columns = {'Length':'Duration'}, inplace = True)


# Convert Reservation column to boolean values
for i in range(len(file)):
    if file.Reservation[i] == "undefined":
        file.loc[i, "Reservation"] = True 
    else:
        file.loc[i, "Reservation"] = False 


# Double-check that file is anonymized
file['Name'] = file['Name'].map(lambda name: name[0:2])


# Data analysis



def duration_describe(df):
    ''' (DataFrame) -> (Series)
    
    Calculates the mean, median, quartiles, stdev, 
    and mode of a list of chat times
    '''
    
    chat_descriptives = df.Duration.describe()
    chat_descriptives['mode'] = df.Duration.mode().loc[0]
    
    return chat_descriptives


def chat_time_count(df):
    ''' (DataFrame -> DataFrame)
    
    Takes a Pandas dataframe with Name (str), Date (Datetime), Duration(int) 
    columns and creates a new dataframe with columns chat_times (str), 
    measured in minutes; chat_count (int), and percent (int)
    Measures statistics about how many chats fall into certain time categories
    '''
    
    chat_time_counts = pd.DataFrame({
                'chat_times' : ['0-5', '5-14', '15-29', '30-44', '45-59', '60+',\
                                '5', '15', '30', '45', '60'],
                'chat_count' : [
                                len(df[(df.Duration >= 0) & (df.Duration <= 5)]),\
                                len(df[(df.Duration > 5) & (df.Duration < 15)]),\
                                len(df[(df.Duration >= 15) & (df.Duration < 30)]),\
                                len(df[(df.Duration >= 30) & (df.Duration < 45)]),\
                                len(df[(df.Duration >= 45) & (df.Duration < 60)]),\
                                len(df[df.Duration >= 60]),\
                                len(df[(df.Duration == 5)]),\
                                len(df[df.Duration == 15]),\
                                len(df[df.Duration == 30]),\
                                len(df[df.Duration == 45]),\
                                len(df[df.Duration == 60])
                                ]
                                    })
    
    chat_time_counts['percent'] = [round(count/len(df.Duration), 2) * 100 \
                    for count in chat_time_counts['chat_count']]
    
    return chat_time_counts

def find_chats_by_duration(df, t1, t2):
    ''' (data frame, int, int) -> int
    Takes in a df of chats and two ints, t1 and t2. 
    Returns a count of all chats with durations between t1 and t2. 
    '''
    count = len(df[(df.Duration >= t1) & (df.Duration <= t2)])
    
    return count

def find_chats_by_duration_2(df, t1, t2):
    '''DataFrame, int, int -> DataFrame
    Takes in a df of chats and two ints, t1 and t2. 
    Returns a DataFrame of all chats with durations between t1 and t2. 
    '''
    chat_df = df[(df.Duration >= t1) & (df.Duration <= t2)]
    
    return chat_df
    

def student_minutes(df, n):
    ''' DataFrame, int -> DataFrame
    Create a dataframe listing n number of students' Talk Time (in minutes)
    sorted in descending order
    '''
    most_minutes_students = df.groupby('Name').sum().nlargest(n, 'Duration').reset_index()
    most_minutes_students.rename(columns = {'Duration':'Talk Time'}, inplace = True)

    return most_minutes_students.reset_index(drop = True)

def student_frequency(df, n):
    ''' dataframe, int -> dataframe
    Takes a cleaned dataframe and a number of students to shop, returns 
    student frequency data, ranked from most sessions to least sessions, 
    displayed to n students.
    Displays Total Chats, % of all chats, Talk Time, % of all talk time
    for n number of students
    '''
    
    # Create a dataframe listing students' total number of chats greater 
    # than 5 minutes, sorted in descending order
    
    # Use student_mins function to find Talk Time for each student
    student_mins = student_minutes(df, len(df))

    # Get df of chats, group by name, and count times name appears       
    most_frequent_students = df.groupby('Name').count()
    # Add the Talk Time column by doing an outer merge with student_mins

    most_frequent_students = pd.merge(most_frequent_students,\
                                        student_mins, on = ['Name'], how = 'outer')
    
    # Clean up some columns/names
    most_frequent_students.rename(columns = {'Date':'Total Chats'}, inplace = True)
    most_frequent_students = most_frequent_students.drop(['Duration'], axis = 1)

    
    # add percentages of total chats/Talk Time
    most_frequent_students['Chat %'] = round((most_frequent_students['Total Chats']\
                          /most_frequent_students['Total Chats'].sum()) * 100, 2)
    
    most_frequent_students['Time %'] = round((most_frequent_students['Talk Time']\
                      /most_frequent_students['Talk Time'].sum()) * 100, 2)
    
    most_frequent_students = most_frequent_students[['Name', 'Total Chats',\
                                                    'Chat %', 'Talk Time',\
                                                    'Time %']]
    
    return most_frequent_students.nlargest(n, 'Total Chats').reset_index(drop = True)

def student_talk_time(df, n):
    student_freq = student_frequency(df, n)
    
    sort_by_time = student_freq.sort_values(['Talk Time'], ascending = False)
    sort_by_time = sort_by_time.reset_index(drop = True)
    
    return sort_by_time

def week_days_data(df):
    days = pd.Series( [0, 0, 0, 0, 0, 0, 0],
            index = [0, 1, 2, 3, 4,\
                     5, 6]
            )
    for date in df.Date:
        weekday = date.weekday()
        days[weekday] += 1
        
    days.index = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday',\
                  'Saturday', 'Sunday']
    
    return days

def months_data(df):
    '''
    Find all the months
    Create a dataframe with Month, Calls, and Minutes columns
    Find the total number of calls and minutes in each month
    '''
    
    # convert index to datetime
    df.set_index(df['Date'], inplace = True)
    #months = pd.DataFrame(columns = ['Month', 'Year', 'Calls', 'Minutes'])
    #months = df.resample('M').count()
    months = df.resample('M').agg({'Calls':'size', 'Minutes':'sum'})
    months.columns = ['Calls', 'Duration', 'Reservation']
    months = months.reset_index()
    months.Date = months['Date'].map(lambda date: pd.to_datetime(date, unit = "M"))
   
    return months
        
def days_data(df):
    '''
    For refined graphing purposes, a list of calls by each individual day
    '''
    
    # convert index to datetime
    df.set_index(df['Date'], inplace = True)

    days = df.resample('D').agg({'Calls':'size', 'Minutes':'sum'})
    days.columns = ['Calls', 'Duration', 'Reservation']
    days.Reservation = days.Reservation.replace(0.0, False)
    days.Reservation = days.Reservation.replace(1.0, True)
    days = weeks.reset_index()
    
    return days

def weeks_data(df):
    '''
    For refined graphing purposes, a list of calls by each individual week
    '''
    
    # convert index to datetime
    df.set_index(df['Date'], inplace = True)

    weeks = df.resample('W').agg({'Calls':'size', 'Minutes':'sum'})
    weeks.columns = ['Calls', 'Duration', 'Reservation']
    weeks.Reservation = weeks.Reservation.replace(0.0, False)
    weeks.Reservation = weeks.Reservation.replace(1.0, True)
    weeks = weeks.reset_index()

    return weeks   

# Store all generated data in appropriate variables
    
# Basic descriptive data on chat durations
duration_descriptives = duration_describe(file)

# Breakdown of chats by duration
chat_time_counts = chat_time_count(file)

# Data on students' total chat count, % of total chats, 
# total talk time, % of total time
# Sorted by total chat count
# Colnames: Name,  Total Chats,  Chat %,  Talk Time,  Time %
student_frequencies = student_frequency(file, len(file))

# Data on students' total chat count, % of total chats, 
# total talk time, % of total time
# Sorted by total talk time
# Colnames: Name,  Total Chats,  Chat %,  Talk Time,  Time %
student_durations = student_talk_time(file, len(file))

# data split into individual points by months, weeks, and days
months = months_data(file)
weeks = weeks_data(file)
days = days_data(file)
# Days with all zero days removed for plotting purposes
    # what the hell why is this so hard
days_no_zeros = days[days['Calls'] != 0]
day_names_data = week_days_data(file)

print(duration_descriptives)
print(chat_time_counts)
print(student_frequencies)
print(student_durations)


'''Visualization with Seaborn'''
sns.set()

# rename DataFrames for easier typing
chat_times = chat_time_counts
freqs = student_frequencies
durations = student_durations


# Plot a histogram of chat times
sns.distplot(file['Duration'], kde = False, color = "red", \
             bins = 10, norm_hist = False)

# With a KDE (Kernel Density Estimate) curve
sns.distplot(file['Duration'], kde = True, color = "red", \
             bins = 10, norm_hist = True)

# Line plot of daily chat times (excluding days with zero)
sns.lineplot(x = 'Date', y = 'Duration', data = days_no_zeros)

# Line plot of total monthly minutes
sns.lineplot(x = 'Date', y = 'Duration', data = months)

months_barplot = sns.barplot(x = 'Date', y = 'Duration', data = months)
months_barplot.set_xticklabels(months_barplot.get_xticklabels(), rotation = 40, ha = "right")
plt.tight_layout()
plt.show()
