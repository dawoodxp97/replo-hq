// @ts-nocheck
import React from 'react';
import ReploInput from './Input';

export default {
  title: 'UI/ReploInput',
  component: ReploInput,
};

const Template = (args) => <ReploInput {...args} />;

export const Text = Template.bind({});
Text.args = {
  kind: 'text',
  placeholder: 'Basic text input',
  allowClear: true,
  size: 'middle',
};

export const TextWithPrefixSuffix = Template.bind({});
TextWithPrefixSuffix.args = {
  kind: 'text',
  placeholder: 'With prefix/suffix',
  prefix: <span>@</span>,
  suffix: <span>.com</span>,
};

export const TextArea = Template.bind({});
TextArea.args = {
  kind: 'textarea',
  placeholder: 'Multi-line input',
  rows: 4,
  autoSize: { minRows: 3, maxRows: 6 },
  showCount: true,
};

export const Search = Template.bind({});
Search.args = {
  kind: 'search',
  placeholder: 'Search something',
  enterButton: true,
  allowClear: true,
};

export const Password = Template.bind({});
Password.args = {
  kind: 'password',
  placeholder: 'Enter password',
  visibilityToggle: true,
};

export const Number = Template.bind({});
Number.args = {
  kind: 'number',
  placeholder: 'Enter number',
  min: 0,
  max: 100,
  step: 1,
};

export const StatusError = Template.bind({});
StatusError.args = {
  kind: 'text',
  placeholder: 'Error status',
  status: 'error',
};

export const AddonBeforeAfter = Template.bind({});
AddonBeforeAfter.args = {
  kind: 'search',
  placeholder: 'With addons',
  addonBefore: <span>https://</span>,
  addonAfter: <span>.org</span>,
};