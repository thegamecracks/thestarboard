# thestarboard

A starboard discord bot written in Python.

![Depiction of a user's cat post starred in a starboard channel](/images/demo.png)

(Photographed by [Makia Minich](https://commons.wikimedia.org/w/index.php?curid=81366278), CC-BY-SA 3.0)

## Contributing

Want to add translations? [Fork this repository], create a new branch,
commit your PO files there, then make a pull request.
See [discord.py-gettext-demo's onboarding] for more information.

[Fork this repository]: https://docs.github.com/en/get-started/quickstart/contributing-to-projects
[discord.py-gettext-demo's onboarding]: https://github.com/thegamecracks/discord.py-i18n-demo/blob/main/docs/en/onboarding.md

## Setup

It is recommended to use [Docker Compose] for running this bot.
To start:

1. Clone this repository:

   ```sh
   git clone https://github.com/thegamecracks/thestarboard
   cd thestarboard
   ```

2. Create a [config.toml] file containing your bot token:

   ```toml
   [bot]
   token = "Bot token from https://discord.com/developers/applications"
   ```

3. Create a [.env] file to be used by Docker Compose:

   ```env
   PGPASSWORD=admin
   ```

4. Start all services using `docker compose up --build --exit-code-from app`

5. To clean up the services, run `docker compose down --volumes`.

If you would like to run the bot in your own system while separately
providing its required services, you can install the bot as a package:

```sh
pip install .
python -m thestarboard
```

Note that Python 3.11 or newer is required.

[Docker Compose]: https://docs.docker.com/get-started/08_using_compose/
[config.toml]: /src/thestarboard/config_default.toml
[.env]: /example.env

## License

This project uses the [MIT] License.

[MIT]: /LICENSE
