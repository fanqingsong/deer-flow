import { forwardRef, useEffect, useImperativeHandle, useState } from "react";
import type { Resource } from "~/core/messages";
import { cn } from "~/lib/utils";

export interface ResourceMentionsProps {
  items: Array<Resource>;
  command: (item: { id: string; label: string }) => void;
}

export const ResourceMentions = forwardRef<
  { onKeyDown: (args: { event: KeyboardEvent }) => boolean },
  ResourceMentionsProps
>((props, ref) => {
  const [selectedIndex, setSelectedIndex] = useState(0);

  const selectItem = (index: number) => {
    const item = props.items[index];

    if (item) {
      props.command({ id: item.uri, label: item.title });
    }
  };

  const upHandler = () => {
    setSelectedIndex(
      (selectedIndex + props.items.length - 1) % props.items.length,
    );
  };

  const downHandler = () => {
    setSelectedIndex((selectedIndex + 1) % props.items.length);
  };

  const enterHandler = () => {
    selectItem(selectedIndex);
  };

  useEffect(() => setSelectedIndex(0), [props.items]);

  useImperativeHandle(ref, () => ({
    onKeyDown: ({ event }) => {
      if (event.key === "ArrowUp") {
        upHandler();
        return true;
      }

      if (event.key === "ArrowDown") {
        downHandler();
        return true;
      }

      if (event.key === "Enter") {
        enterHandler();
        return true;
      }

      return false;
    },
  }));

  return (
    <div className="relative flex flex-col gap-0.5 overflow-auto rounded-md border border-gray-100 bg-white p-1 shadow">
      {props.items.length ? (
        props.items.map((item, index) => (
          <button
            className={cn(
              "flex w-full items-center gap-1 rounded-sm px-1 py-0.5 text-sm hover:bg-gray-100",
              selectedIndex === index && "bg-gray-50",
            )}
            key={index}
            onClick={() => selectItem(index)}
          >
            {item.title}
          </button>
        ))
      ) : (
        <div className="items-center justify-center text-gray-500">
          No result
        </div>
      )}
    </div>
  );
});
