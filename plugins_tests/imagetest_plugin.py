import os
import random

HELP_DESC = "!imagetest\t\t-\tSend back test image\n"


async def register_to(plugin):

    # Echo back the given command
    async def imagetest_callback(room, event):
        exts = ["gif", "jpg", "png", "jpeg"]
        images = filter(
            lambda x: any(x.lower().endswith(ext) for ext in exts), os.listdir()
        )
        await plugin.send_image(random.choice(list(images)))

    # Add a command handler waiting for the echo command
    imagetest_handler = plugin.CommandHandler("imagetest", imagetest_callback)
    plugin.add_handler(imagetest_handler)
