#!/bin/bash

clear

cat << "EOF"

        _______________________________________
       /                                      /|
      /______________________________________/ |
      |                                      | |
      |  > docker compose up --build         | |
      |  > postgres ready...                 | |
      |  > resume intelligence online        | |
      |______________________________________|/
             \   ^__^
              \  (••)\_______
                 (__)\       )\/\
                      ||----w |
                      ||     ||

             👨‍💻 Happy Coding!

EOF

figlet "PostgreSQL"

echo "🚀 Resume Intelligence Database"
echo "================================"
echo

exec docker-entrypoint.sh "$@"
