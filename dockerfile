FROM public.ecr.aws/lambda/python:3.10

RUN yum install -y \
    tar gzip xz wget \
    fontconfig freetype \
    libXinerama libXrandr libXrender libXext libSM \
    cups-libs dbus-glib \
    cairo pango atk at-spi2-atk gtk3 \
    && yum clean all

RUN wget https://downloadarchive.documentfoundation.org/libreoffice/old/7.6.2.1/rpm/x86_64/LibreOffice_7.6.2.1_Linux_x86-64_rpm.tar.gz -O /tmp/lo.tar.gz \
 && tar -xzf /tmp/lo.tar.gz -C /tmp \
 && yum localinstall -y /tmp/LibreOffice_*/RPMS/*.rpm \
 && rm -rf /tmp/LibreOffice_* /tmp/lo.tar.gz

# ✅ Fix: create a known symlink so your code can find soffice reliably
RUN ln -sf /opt/libreoffice7.6/program/soffice /usr/bin/soffice

COPY app.py ${LAMBDA_TASK_ROOT}

CMD ["app.lambda_handler"]