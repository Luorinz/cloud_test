import os

import MySQLdb
import webapp2


# These environment variables are configured in app.yaml.
CLOUDSQL_CONNECTION_NAME = os.environ.get('CLOUDSQL_CONNECTION_NAME')
CLOUDSQL_USER = os.environ.get('CLOUDSQL_USER')
CLOUDSQL_PASSWORD = os.environ.get('CLOUDSQL_PASSWORD')


def connect_to_cloudsql():
    # When deployed to App Engine, the `SERVER_SOFTWARE` environment variable
    # will be set to 'Google App Engine/version'.
    if os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine/'):
        # Connect using the unix socket located at
        # /cloudsql/cloudsql-connection-name.
        cloudsql_unix_socket = os.path.join(
            '/cloudsql', CLOUDSQL_CONNECTION_NAME)

        db = MySQLdb.connect(
            unix_socket=cloudsql_unix_socket,
            user=CLOUDSQL_USER,
            passwd=CLOUDSQL_PASSWORD)

    # If the unix socket is unavailable, then try to connect using TCP. This
    # will work if you're running a local MySQL server or using the Cloud SQL
    # proxy, for example:
    #
    #   $ cloud_sql_proxy -instances=your-connection-name=tcp:3306
    #
    else:
        db = MySQLdb.connect(
            host='127.0.0.1', user=CLOUDSQL_USER, passwd=CLOUDSQL_PASSWORD)

    return db


def execute_sql(s):
    db = connect_to_cloudsql()
    cursor = db.cursor()

    # Local test
    # cursor.execute('use test')

    cursor.execute('use Steps;')
    cursor.execute(s)
    db.commit()
    return cursor.fetchall()


class UpdateHandler(webapp2.RequestHandler):
    def post(self, userID, day, hour, step):
        self.response.headers['Content-Type'] = 'text/plain'
        if int(day) < 0 or int(hour) < 0 or int(step) < 0 or int(hour) > 23 or int(step) > 5000:
            self.response.write('invalid number')
            self.response.set_status(400)
        else:
            hour_col = "h" + hour
            update_hour = "insert into Hour(user,day,{2},step) values('{0}',{1},{3},{3}) on duplicate key update step = step + values({2}) - {2},{2} = values({2});".format(userID, day, hour_col, step)
            execute_sql(update_hour)
            self.response.write("successfully added/update")



class CurrentDayHandler(webapp2.RequestHandler):
    # Todo: query for the stepcounts in the latest day in the database
    def get(self, userID):
        sql = "select day,step from Hour where user = '{}'".format(userID)
        results = execute_sql(sql)
        latest = 0
        res = 0
        for i in results:
            if int(i[0]) > latest:
                latest = int(i[0])
                res = int(i[1])

        if results == ():
            self.response.write("User {} doesn't exist.".format(userID))
        else:
            self.response.write('Total step count on day {} for {} is {}'.format(latest, userID, res))


class SingleDayHandler(webapp2.RequestHandler):
    def get(self, userID, day):
        sql = "select step from Hour where user = '{}' and day = {} ".format(userID, day)
        results = execute_sql(sql)

        if not results:
            self.response.write("Failed")
        else:

            self.response.write('Total step count on day {} for {} is {}'.format(day, userID, results[0][0]))


class RangeDayHandler(webapp2.RequestHandler):
    def get(self, userID, startDay, numDays):
        sql = "select step from Hour where user = '{}' and day >= {} and day <= {}".format(userID,startDay,int(startDay)+int(numDays)-1)
        results = execute_sql(sql)
        if not results:
            self.response.write("Failed")
        else:
            sum = 0
            for i in results:
                sum += int(i[0])
            self.response.write('Total step count from day {} to day {} for {} is {}'.format(startDay, int(startDay)+int(numDays)-1, userID, sum))


class DeleteHandler(webapp2.RequestHandler):
    def get(self):
        sql = "truncate Hour;"
        execute_sql(sql)
        self.response.write("Database deleted")

class MainPage(webapp2.RequestHandler):
    def get(self):
        """Simple request handler that shows all of the MySQL variables."""

        self.response.headers['Content-Type'] = 'text/html'
        self.response.charset = "UTF-8"

        #Test for the project
        self.response.write(
            '<html><body>'
            '<h1>Usage</h1>'
            '<p>To create/update a step count. Endpoint:/{userID}/{day}/{hour}/{step} Method:POST</p>'
            'e.g. /user1/1/0/42'
            '<p>To retrieve the step count sum for the latest day in the database. Endpoint:/current/{userID} Method:GET</p>'
            'e.g. /current/user1'
            '<p>To retrieve the step count sum for a single day. Endpoint:/single/{userID}/{day} Method:GET</p>'
            'e.g. /single/user1/1'
            '<p>To retrieve the step count sum for a range of days. Endpoint:/range/{userID}/{start_day}/{day_number} Method:GET</p>'
            'e.g. /range/user1/1/3, start day must be earier than the latest day in the database'
            '<p>To empty the database. Endpoint:/delete Method:DELETE</p>'
            '<br />'
            '<p>userID: string e.g. user1, user2</p>'
            '<p>day, start_day, day_number: positive integer number</p>'
            '<p>hour: select an integer from 0 to 23</p>'
            '<p>step: non-negative integer number</p>'
            '<br />'
            '<a href="https://docs.google.com/document/d/1y4u422Btu3qJbLFZcJbS9jrbiVUJHNPL_3fDjUH72rA">Document</a>'
            '</body></html>'
                            )

        sql = "select user,day,step from Hour;"

        results = execute_sql(sql)
        self.response.write("\n")
        show_data = '<p>'
        for row in results :
            for i in row:
                show_data += str(i) + "\t"
            show_data += '</p>'
            self.response.write(show_data)
            show_data = '<p>'



app = webapp2.WSGIApplication([
    ('/', MainPage),
    webapp2.Route('/current/<userID:(.*)>', handler=CurrentDayHandler, name='CurrentDay'),
    webapp2.Route('/single/<userID:(.*)>/<day:([1-9][0-9]*)>', handler=SingleDayHandler, name='SingleDay'),
    webapp2.Route('/range/<userID:(.*)>/<startDay:([1-9][0-9]*)>/<numDays:(\d+)>', handler=RangeDayHandler, name='RangeDay'),
    webapp2.Route('/<userID:(.*)>/<day:([1-9][0-9]*)>/<hour:(\d+)>/<step:(\d+)>', handler=UpdateHandler, handler_method='post', name='Update'),
    webapp2.Route('/delete', handler=DeleteHandler, name='Delete')

], debug=True)