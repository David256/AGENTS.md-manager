import os
import pathlib
import re
import time

from watchdog.observers import Observer
from watchdog.events import DirModifiedEvent, FileModifiedEvent, FileSystemEventHandler


re_tag = re.compile(r'<!--\s*@([\w.-]+)\s*-->')


def build_tag(tag: str):
    return f'<!-- @{tag} -->'


def render_template(template_name: str, tag_target: str | None):
    template_filename = f'./template/{template_name}.md'
    if not os.path.exists(template_filename):
        print('Cannot find template', template_name)
        return

    # read the file content
    with open(template_filename, 'r') as fd:
        template_content = fd.read()

    # get the tags
    tags: list[str] = re_tag.findall(template_content)
    if len(tags) == 0:
        print('No tags found')
        return

    # Check if the target is in the file content
    if tag_target is not None and tag_target not in tags:
        return

    # Now...
    print('re-render', template_name)

    for tag in tags:
        # read the tag content
        resource_filename = f'./resources/{tag}.md'
        with open(resource_filename, 'r') as fd:
            resource_content = fd.read()
        # remplace the tag
        template_content = template_content.replace(
            build_tag(tag),
            resource_content,
        )
    # save the template in the generated directory
    with open(f'./generated/{template_name}.md', 'w') as fd:
        fd.write(template_content)


class ResourceWatcher(FileSystemEventHandler):
    def on_modified(self, event: DirModifiedEvent | FileModifiedEvent) -> None:
        src_path = (
            event.src_path.decode()
            if isinstance(event.src_path, bytes)
            else event.src_path
        )
        tag_target: str | None = None
        template_target: str | None = None
        if isinstance(event, DirModifiedEvent):
            # render all templates
            # print('render all templates')
            # ignored for now
            return
        elif isinstance(event, FileModifiedEvent):
            # update only one file
            changed_filename = os.path.basename(src_path)
            changed_name, changed_ext = os.path.splitext(
                changed_filename)
            if changed_ext.lower() != '.md':
                return
            # print('render', resource_name)
            dirname = os.path.dirname(src_path)
            if pathlib.Path(dirname).resolve() == pathlib.Path('./resources').resolve():
                tag_target = changed_name
            elif pathlib.Path(dirname).resolve() == pathlib.Path('./template').resolve():
                template_target = changed_name
            else:
                print('unknown path:', dirname)
                return

        if template_target:
            print('template changed')
            render_template(template_target, tag_target)
            return

        # find the template that use that modified file
        for scanned in os.scandir('./template'):
            if scanned.is_dir():
                continue

            # ignore non-markdown file
            template_filename = os.path.basename(scanned.path)
            template_name, template_ext = os.path.splitext(
                template_filename)
            if template_ext.lower() != '.md':
                continue

            render_template(template_name, tag_target)

    # no more events

observer = Observer()

observer.schedule(
    ResourceWatcher(),
    './resources',
    recursive=False,
)

observer.schedule(
    ResourceWatcher(),
    './template',
    recursive=False,
)

# ...
observer.start()

try:
    while True:
        time.sleep(0.1)
except:
    observer.stop()
    observer.join()
