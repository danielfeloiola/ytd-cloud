import os
from application import app

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000)
    #app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
    #app.run()
