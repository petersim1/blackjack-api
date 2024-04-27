FROM python:3.11

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3.11 -

# Set the PATH for Poetry
ENV PATH /root/.local/bin:$PATH

# Set the working directory
WORKDIR /app

# Copy the project files into the Docker image
COPY . /app

# Install the project dependencies with Poetry
RUN poetry config virtualenvs.create false \
  && poetry install --no-dev --no-cache

# Run the Makefile command
CMD ["make", "run"]