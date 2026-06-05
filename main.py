from app.app import create_app
import logging

app = create_app()


if __name__ == '__main__':
    logging.info("我是info级别的日志")
    logging.debug("我是debug级别的日志")
    app.run()
    # app.run(debug=True)
    # print(app.url_map)
