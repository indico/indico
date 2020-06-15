// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {shallow, mount} from 'enzyme';
import {act} from 'react-dom/test-utils';

import mockAxios from 'jest-mock-axios';
import React from 'react';

import * as axiosUtils from 'indico/utils/axios';

import * as actions from '../actions';
import FileManager, {Dropzone} from '..';

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
    extensions: ['txt', 'md', 'tex'],
    allowMultipleFiles: false,
  },
  {
    id: 2,
    name: 'PDF file',
    extensions: ['pdf'],
    allowMultipleFiles: false,
  },
  {
    id: 3,
    name: 'Image files',
    extensions: ['png'],
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
    mockAxios.mockResponseFor('goes://nowhere', {
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

function getDropzoneForFileType(wrapper, id) {
  return wrapper
    .find('FileType')
    .find(Dropzone)
    .filterWhere(d => d.prop('fileType').id === id)
    .find('Dropzone');
}

async function uploadFile(dropzone, onChange, name, type, deletedFile = null) {
  const uuid = await simulateFileUpload(dropzone, name, type);
  expect(onChange).toHaveBeenCalledWith({'2': [uuid]});
  if (deletedFile) {
    const deleteUrl = `flask://files.delete_file/uuid=${deletedFile}`;
    expect(mockAxios.delete).toHaveBeenCalledWith(deleteUrl);
    await act(async () => {
      mockAxios.mockResponseFor(deleteUrl, undefined);
    });
  } else {
    expect(mockAxios.delete).not.toHaveBeenCalled();
  }
  onChange.mockClear();
  mockAxios.delete.mockClear();
  return uuid;
}

function getFileEntryForFileType(wrapper, fileTypeId) {
  return wrapper.find('FileEntry').filterWhere(x => x.prop('fileType').id === fileTypeId);
}

function checkFileEntry(fileEntry, name, icon) {
  expect(fileEntry.find('span:first-child').text()).toEqual(name);
  expect(fileEntry.find('FileAction').prop('icon')).toEqual(icon);
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
        invalidFiles: [],
        uploadableFiles: [],
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

    const dropzone = getDropzoneForFileType(wrapper, 2);

    // upload a new file
    await uploadFile(dropzone, onChange, 'test1.pdf', 'pdf');
    wrapper.update();
    checkFileEntry(getFileEntryForFileType(wrapper, 2), 'test1.pdf', 'trash');

    // replace the newly uploaded file
    const uuid = await uploadFile(dropzone, onChange, 'test2.pdf', 'pdf', 'newtest1.pdf');
    wrapper.update();
    const fileEntry = getFileEntryForFileType(wrapper, 2);
    checkFileEntry(fileEntry, 'test2.pdf', 'trash');

    // perform an undo - this needs to go back to an empty file list
    await act(async () => {
      fileEntry.find('FileAction').simulate('click');
      mockAxios.mockResponseFor(`flask://files.delete_file/uuid=${uuid}`, undefined);
    });
    expect(mockAxios.delete).toHaveBeenCalledWith(`flask://files.delete_file/uuid=${uuid}`);
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

    const dropzone = getDropzoneForFileType(wrapper, 2);

    // upload a file which replaces the initial one
    await uploadFile(dropzone, onChange, 'test1.pdf', 'pdf');
    wrapper.update();
    checkFileEntry(getFileEntryForFileType(wrapper, 2), 'test1.pdf', 'undo');

    // replace the newly uploaded file
    const uuid = await uploadFile(dropzone, onChange, 'test2.pdf', 'pdf', 'newtest1.pdf');
    wrapper.update();
    const fileEntry = getFileEntryForFileType(wrapper, 2);
    checkFileEntry(fileEntry, 'test2.pdf', 'undo');

    // perform an undo - this needs to revert to the initial file!
    await act(async () => {
      fileEntry.find('FileAction').simulate('click');
      mockAxios.mockResponseFor(`flask://files.delete_file/uuid=${uuid}`, undefined);
    });
    expect(mockAxios.delete).toHaveBeenCalledWith(`flask://files.delete_file/uuid=${uuid}`);
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
    const dropzone = getDropzoneForFileType(wrapper, 2);

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
      mockAxios.mockResponseFor('http://upload/endpoint', {
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
    const fileEntry = getFileEntryForFileType(wrapper, 2);
    expect(fileEntry.find('span:first-child').text()).toEqual('test.pdf');
    expect(fileEntry.find('FileAction').prop('icon')).toEqual('undo');
  });

  it('handles upload errors properly', async () => {
    // eslint-disable-next-line import/namespace, no-import-assign
    axiosUtils.handleAxiosError = jest
      .spyOn(axiosUtils, 'handleAxiosError')
      .mockImplementation(() => {});

    const onChange = jest.fn();
    const wrapper = mount(
      <FileManager
        uploadURL="goes://nowhere"
        downloadURL="goes://nowhere"
        fileTypes={[fileTypes[1]]}
        onChange={onChange}
      />
    );

    const dropzone = getDropzoneForFileType(wrapper, 2);
    const file1 = {type: 'pdf', name: 'test.pdf'};

    // simulate actual "drop" event
    await act(async () => {
      dropzone.simulate('drop', createDtWithFiles([file1]));
    });

    await act(async () => {
      mockAxios.mockError();
    });

    const mockDispatch = React.mockDispatches[0];

    expect(mockDispatch).toHaveBeenCalledWith(
      expect.objectContaining({type: actions.UPLOAD_ERROR})
    );
    expect(onChange).not.toHaveBeenCalled();

    wrapper.update();

    const fileEntry = getFileEntryForFileType(wrapper, 2);
    expect(fileEntry.exists()).toEqual(false);
    expect(
      wrapper
        .find('FileType')
        .find('Uploads')
        .find('.error')
        .exists()
    ).toEqual(true);

    axiosUtils.handleAxiosError.mockRestore();
  });
});
