
# Use the official Frappe Docker image as a base
FROM frappe/frappe-nginx:latest

# Copy the lms_app to the apps directory
COPY . /opt/frappe/apps/lms_app

# Install the app
RUN bench --site all install-app lms_app
