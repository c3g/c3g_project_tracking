FROM fedora:36
ENV APP=project_tracking

RUN mkdir /app /sqlite
WORKDIR /app


RUN dnf install -y python3-pip.noarch
ENV C3G_SQLALCHEMY_DATABASE_URI="sqlite:////sqlite/tracking_db.sql"

ADD .  $APP
RUN cd $APP && pip install . && chmod 755 entrypoint.sh && mv entrypoint.sh .. 

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh", "-b", "0.0.0.0"]
CMD ["-w", "4"]
