


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



class CurrentDayHandler(webapp2.RequestHandler):
    def get(self, userID):
        self.response.headers['Content-Type'] = 'text/plain'

        db = connect_to_cloudsql()
        cursor = db.cursor()

        sql1 = "use Steps"
        sql2 = "select * from StepCounts where userID = '{}'".format(userID)

        cursor.execute(sql1)
        cursor.execute(sql2)

        results = cursor.fetchall()


        # update_record_key = ndb.Key(UpdateRecord, userID)
        # update_record = update_record_key.get()
        #
        # if update_record is None:
        #     self.response.write('user {} not found'.format(userID))
        #     return
        #
        # day = update_record.mostRecentDay
        # step_record_key = ndb.Key(StepRecord, userID + '#' + day)
        # step_record = step_record_key.get()
        if results is ():
            self.response.write("User {} doesn't exist.".format(userID))
        else:
            self.response.write('Total step count on day {} for {} is {}'.format(results[0][2], userID, results[0][6]))






class MainPage(webapp2.RequestHandler):
    def get(self):
        """Simple request handler that shows all of the MySQL variables."""
        self.response.headers['Content-Type'] = 'text/plain'

        #Connect to cloudSQL
        db = connect_to_cloudsql()
        cursor = db.cursor()
        # cursor.execute('SHOW VARIABLES')
        #
        # for r in cursor.fetchall():
        #     self.response.write('{}\n'.format(r))
        # self.response.write(("Anda is learning this stuff!"))

        #Test for entering the mysql
        sql1 = "use Steps"
        sql2 = "select * from StepCounts"

        cursor.execute(sql1)  #
        cursor.execute(sql2)
        results = cursor.fetchall()	#
        self.response.write("ID userID day hour step\n")	#
        for row in results :
            ID = row[0]
            userID = row[1]
            day = row[2]
            hour = row[3]
            step = row[6]

            self.response.write(ID)
            self.response.write(userID)

            self.response.write(day)
            self.response.write(hour)
            self.response.write(step)
            self.response.write('\n')


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
            '</body></html>')




app = webapp2.WSGIApplication([
    ('/', MainPage),
    # ('/current/(.*)', CurrentDayHandler),
    webapp2.Route('/current/<userID:(.*)>', handler=CurrentDayHandler, name='blog-archive'),

], debug=True)