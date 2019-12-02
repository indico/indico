// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {shallow, mount} from 'enzyme';
import {act} from 'react-dom/test-utils';

import mockAxios from 'jest-mock-axios';
import React from 'react';

import FileManager, {Dropzone} from '../components/FileManager';
import * as actions from '../components/FileManager/actions';

expect.extend({
  toContainFile(received, file) {
    const receivedFile = received.get('file');
    return {
      pass: receivedFile.name === file.name && receivedFile.type === file.type,
      message: 'Files should match',
    };
  },
});

const fileTypes = [
  {
    id: 1,
    name: 'Source file',
    extensions: ['.txt', '.md', '.tex'],
    allowMultipleFiles: false,
  },
  {
    id: 2,
    name: 'PDF file',
    extensions: ['.pdf'],
    allowMultipleFiles: false,
  },
  {
    id: 3,
    name: 'Image files',
    extensions: ['.png'],
    allowMultipleFiles: true,
  },
];

const fileList = [
  {
    filename: 'file1.txt',
    downloadURL: 'url://file1.txt',
    uuid: 'file1',
    claimed: true,
    fileType: 1,
  },
  {
    filename: 'file1.pdf',
    downloadURL: 'url://file1.pdf',
    uuid: 'file2',
    claimed: true,
    fileType: 2,
  },
  {
    filename: 'image.png',
    downloadURL: 'url://image.png',
    uuid: 'file3',
    claimed: true,
    fileType: 3,
  },
  {
    filename: 'image2.png',
    downloadURL: 'url://image2.png',
    uuid: 'file4',
    claimed: true,
    fileType: 4,
  },
];

afterEach(() => {
  // cleaning up the mess left behind the previous test
  mockAxios.reset();
  React.resetMocks();
});

function createDtWithFiles(files = []) {
  files = files.map(({content, name, type}) => new File([content], name, {type}));
  return {
    dataTransfer: {
      files,
      items: files.map(file => ({
        kind: 'file',
        size: file.size,
        type: file.type,
        getAsFile: () => file,
      })),
      types: ['Files'],
    },
  };
}

async function simulateFileUpload(dropzone, name, type) {
  const uuid = `new${name}`;

  await act(async () => {
    dropzone.simulate('drop', createDtWithFiles([{type, name}]));
  });

  await act(async () => {
    mockAxios.mockResponse({
      data: {
        uuid,
        filename: name,
        claimed: false,
        downloadURL: 'goes://nowhere',
      },
    });
  });

  return uuid;
}

describe('File manager', () => {
  it('renders OK', () => {
    const wrapper = shallow(
      <FileManager
        uploadURL="goes://nowhere"
        downloadURL="goes://nowhere"
        fileTypes={fileTypes}
        files={fileList}
        onChange={() => null}
      />
    );
    expect(wrapper.find('FileType')).toHaveLength(3);
    wrapper.find('FileType').forEach((node, i) => {
      expect(node.prop('fileType')).toEqual({
        ...fileTypes[i],
        files: fileList.filter(f => f.fileType === i + 1),
      });
      expect(node.prop('uploads')).toEqual({});
    });
  });

  it('lets you upload a new file', async () => {
    const onChange = jest.fn();
    const wrapper = mount(
      <FileManager
        uploadURL="goes://nowhere"
        downloadURL="goes://nowhere"
        fileTypes={[fileTypes[1]]}
        onChange={onChange}
      />
    );

    const dropzone = wrapper
      .find('FileType')
      .find(Dropzone)
      .filterWhere(d => d.prop('fileType').id === 2)
      .find('Dropzone');

    const uuid1 = await simulateFileUpload(dropzone, 'test1.pdf', 'pdf');
    expect(onChange).toHaveBeenCalledWith({'2': [uuid1]});
    expect(mockAxios.delete).not.toHaveBeenCalled();
    onChange.mockClear();

    // upload another file which should replace the previous one
    const uuid2 = await simulateFileUpload(dropzone, 'test2.pdf', 'pdf');
    expect(onChange).toHaveBeenCalledWith({'2': [uuid2]});
    expect(mockAxios.delete).toHaveBeenCalledWith('/files/newtest1.pdf');
    await act(async () => {
      mockAxios.mockResponse(); // respond to the DELETE request
    });
    onChange.mockClear();
    mockAxios.delete.mockClear();

    wrapper.update();
    const fileEntry = wrapper.find('FileEntry').find({fileTypeId: 2});
    const fileAction = fileEntry.find('FileAction');
    expect(fileEntry.find('span:first-child').text()).toEqual('test2.pdf');
    expect(fileAction.prop('icon')).toEqual('trash');

    await act(async () => {
      fileAction.simulate('click');
      mockAxios.mockResponse(); // respond to the DELETE request
    });

    expect(mockAxios.delete).toHaveBeenCalledWith('/files/newtest2.pdf');
    expect(onChange).toHaveBeenCalledWith({});
  });

  it('lets you upload a file, replacing an existing one', async () => {
    const onChange = jest.fn();
    const wrapper = mount(
      <FileManager
        uploadURL="goes://nowhere"
        downloadURL="goes://nowhere"
        fileTypes={fileTypes}
        onChange={onChange}
        files={[
          {
            filename: 'file1.pdf',
            downloadURL: 'url://file1.pdf',
            uuid: 'file1',
            claimed: true,
            fileType: 2,
          },
        ]}
      />
    );

    const dropzone = wrapper
      .find('FileType')
      .find(Dropzone)
      .filterWhere(d => d.prop('fileType').id === 2)
      .find('Dropzone');

    const uuid1 = await simulateFileUpload(dropzone, 'test1.pdf', 'pdf');
    expect(onChange).toHaveBeenCalledWith({'2': [uuid1]});
    onChange.mockClear();

    // upload another file which should replace the previous one
    const uuid2 = await simulateFileUpload(dropzone, 'test2.pdf', 'pdf');
    expect(onChange).toHaveBeenCalledWith({'2': [uuid2]});
    expect(mockAxios.delete).toHaveBeenCalledWith('/files/newtest1.pdf');
    await act(async () => {
      mockAxios.mockResponse(); // respond to the DELETE request
    });
    onChange.mockClear();
    mockAxios.delete.mockClear();

    wrapper.update();
    const fileEntry = wrapper.find('FileEntry').find({fileTypeId: 2});
    const fileAction = fileEntry.find('FileAction');
    expect(fileEntry.find('span:first-child').text()).toEqual('test2.pdf');
    expect(fileAction.prop('icon')).toEqual('undo');

    await act(async () => {
      fileAction.simulate('click');
      mockAxios.mockResponse(); // respond to the DELETE request
    });

    expect(mockAxios.delete).toHaveBeenCalledWith('/files/newtest2.pdf');
    expect(onChange).toHaveBeenCalledWith({'2': ['file1']});
  });

  it('modifies an existing file', async () => {
    const onChange = jest.fn();
    const wrapper = mount(
      <FileManager
        uploadURL="http://upload/endpoint"
        downloadURL="http://download/endpoint"
        fileTypes={fileTypes}
        files={fileList}
        onChange={onChange}
      />
    );
    const dropzone = wrapper
      .find('FileType')
      .find(Dropzone)
      .filterWhere(d => d.prop('fileType').id === 2)
      .find('Dropzone');

    const file1 = {type: 'pdf', name: 'test.pdf'};

    // simulate actual "drop" event
    await act(async () => {
      dropzone.simulate('drop', createDtWithFiles([file1]));
    });

    const mockDispatch = React.mockDispatches[0];

    // the upload endpoint is properly called
    expect(mockAxios.post).toHaveBeenCalledWith(
      'http://upload/endpoint',
      expect.toContainFile(file1),
      expect.anything()
    );

    // the internal state is updated
    expect(mockDispatch).toHaveBeenCalledWith(
      expect.objectContaining({type: actions.START_UPLOADS})
    );

    expect(onChange).not.toHaveBeenCalled();

    await act(async () => {
      mockAxios.mockResponse({
        data: {
          uuid: 'newfile2',
          filename: file1.name,
          claimed: false,
          downloadURL: 'goes://nowhere',
        },
      });
    });

    // once the upload finished, the state is updated
    expect(mockDispatch).toHaveBeenCalledWith(
      expect.objectContaining({type: actions.MARK_MODIFIED})
    );

    expect(onChange).toHaveBeenCalledWith({'1': ['file1'], '2': ['newfile2'], '3': ['file3']});

    wrapper.update();

    // modified file renders properly
    const fileEntry = wrapper.find('FileEntry').find({fileTypeId: 2});
    expect(fileEntry.find('span:first-child').text()).toEqual('test.pdf');
    expect(fileEntry.find('FileAction').prop('icon')).toEqual('undo');
  });
});
