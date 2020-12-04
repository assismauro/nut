from flask import Flask, render_template, request
import common
from datetime import datetime

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = '142957'

@app.teardown_appcontext
def close_db(error):
    common.closeDb()

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        date = request.form['date'] #assuming the date is in YYYY-MM-DD format

        dt = datetime.strptime(date, '%Y-%m-%d')
        database_date = datetime.strftime(dt, '%Y%m%d')

        common.executeIUD('insert into log_date (entry_date) values (%s)', (database_date,))

    results = common.getDataFromDb(
        '''select log_date.entry_date, sum(food.protein) as protein, 
              sum(food.carbohydrates) as carbohydrates, 
              sum(food.fat) as fat, sum(food.calories) as calories
             from log_date 
       inner join food_date on food_date.log_date_id = log_date.id 
       inner join food on food.id = food_date.food_id 
group by log_date.entry_date order by 1''')

    date_results = []

    for i in results:
        single_date = {}

        single_date['entry_date'] = i['entry_date']

        d = datetime.strptime(str(i['entry_date']), '%Y-%m-%d')
        single_date['pretty_date'] = datetime.strftime(d, '%B %d, %Y')

        date_results.append(single_date)

    return render_template('home.html', results=date_results)

@app.route('/view/<date>', methods=['GET', 'POST']) #date is going to be 20170520
def view(date):

    date_result = common.getDataFromDb('select id, entry_date from log_date where entry_date = %s', (date,))
    if date_result == []:
        common.executeIUD('insert into log_date(entry_date) values (%s)',(date,))
        date_result = common.getDataFromDb('select id, entry_date from log_date where entry_date = %s', (date,))

    if request.method == 'POST':
        common.executeIUD('insert into food_date (food_id, log_date_id) values (%s, %s)',
                          (request.form['food-select'], date_result[0]['id']))

    d = datetime.strptime(str(date_result[0]['entry_date']), '%Y-%m-%d')
    pretty_date = datetime.strftime(d, '%B %d, %Y')

    food_results = common.getDataFromDb('select id, name from food')

    log_results = common.getDataFromDb(
        'select food.name, food.protein, food.carbohydrates, food.fat, food.calories from log_date \
           join food_date on food_date.log_date_id = log_date.id \
           join food on food.id = food_date.food_id where log_date.entry_date = %s', (date,))

    totals = common.getDataFromDb(
        '''select sum(food.protein) as protein, 
         sum(food.carbohydrates) as carbohydrates, 
         sum(food.fat) as fat, sum(food.calories) as calories
         from log_date 
         inner join food_date on food_date.log_date_id = log_date.id 
         inner join food on food.id = food_date.food_id 
         where food_date.log_date_id = %s''', (date_result[0]['id'],))
    return render_template('day.html', entry_date=date_result[0]['entry_date'],
                           pretty_date=pretty_date, food_results=food_results, log_results=log_results, totals=totals[0])

@app.route('/food', methods=['GET', 'POST'])
def food():
    if request.method == 'POST':
        name = request.form['food-name']
        protein = int(request.form['protein'])
        carbohydrates = int(request.form['carbohydrates'])
        fat = int(request.form['fat'])

        calories = protein * 4 + carbohydrates * 4 + fat * 9

        common.executeIUD('insert into food (name, protein, carbohydrates, fat, calories) values (%s, %s, %s, %s, %s)',
            (name, protein, carbohydrates, fat, calories))

    results = common.getDataFromDb('select name, protein, carbohydrates, fat, calories from food')

    return render_template('add_food.html', results=results)

if __name__ == '__main__':
    app.run(debug=True)