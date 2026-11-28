// A minimal stand-in for the DOM, enough to run the init() of a page script under node --test
// without a browser or a dependency: elements with attributes, children, text, value and
// event listeners, and a document that finds them by id. Not a test file (*.test.mjs).

class FakeElement {
  constructor(doc, tag) {
    this.ownerDocument = doc;
    this.tagName = tag.toUpperCase();
    this.attributes = new Map();
    this.children = [];
    this.listeners = {};
    this.value = "";
    this.hidden = false;
    this.ownText = "";
  }

  get id() { return this.attributes.get("id") || ""; }

  setAttribute(name, value) {
    this.attributes.set(name, String(value));
    if (name === "id") this.ownerDocument.byId.set(String(value), this);
  }

  getAttribute(name) { return this.attributes.has(name) ? this.attributes.get(name) : null; }
  hasAttribute(name) { return this.attributes.has(name); }
  removeAttribute(name) { this.attributes.delete(name); }

  appendChild(child) {
    this.children.push(child);
    return child;
  }

  get textContent() { return this.ownText + this.children.map((c) => c.textContent).join(""); }

  set textContent(text) {
    this.ownText = String(text);
    this.children = [];
  }

  addEventListener(type, listener) { (this.listeners[type] = this.listeners[type] || []).push(listener); }

  // Calls the listeners of one event type; props are copied onto the event (key, for example).
  fire(type, props) {
    const event = Object.assign({ type, preventDefault() {} }, props);
    (this.listeners[type] || []).forEach((listener) => listener(event));
    return event;
  }
}

export function fakeDocument() {
  const doc = {
    byId: new Map(),
    getElementById(id) { return this.byId.get(id) || null; },
    createElement(tag) { return new FakeElement(this, tag); },
  };
  return doc;
}

// An element with an id and attributes, registered in the document.
export function add(doc, tag, id, attributes) {
  const node = doc.createElement(tag);
  node.setAttribute("id", id);
  Object.entries(attributes || {}).forEach(([k, v]) => node.setAttribute(k, v));
  return node;
}
