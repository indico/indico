import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Sidebar, Table, Checkbox} from 'semantic-ui-react';

export default function SideBar({filterType}) {
  const [speakerValue, setSpeakerValue] = useState('');
  const handleChange = (e, {value}) => {
    setSpeakerValue(speakerValue === value ? '' : value);
  };
  // it's going to change soon
  if (filterType !== 'Contributions') return;
  return (
    <Sidebar animation="push" direction="left" visible width="thin" icon="labeled">
      <Table celled padded>
        <Table.Header>
          <Table.Row>
            <Table.HeaderCell>Speakers</Table.HeaderCell>
          </Table.Row>
        </Table.Header>

        <Table.Body>
          <Table.Row>
            <Table.Cell>
              <Checkbox
                label="Aristofanis (45)"
                name="Aristofanis"
                value="Aristofanis"
                checked={speakerValue === 'Aristofanis'}
                onChange={handleChange}
              />
            </Table.Cell>
          </Table.Row>
          <Table.Row>
            <Table.Cell>
              <Checkbox
                label="Pedro (4555)"
                name="Pedro"
                value="Pedro"
                checked={speakerValue === 'Pedro'}
                onChange={handleChange}
              />
            </Table.Cell>
          </Table.Row>
          <Table.Row>
            <Table.Cell>
              <Checkbox
                label="Adrian (455)"
                name="Adrian"
                value="Adrian"
                checked={speakerValue === 'Adrian'}
                onChange={handleChange}
              />
            </Table.Cell>
          </Table.Row>
        </Table.Body>
      </Table>

      <Table celled padded>
        <Table.Header>
          <Table.Row>
            <Table.HeaderCell>Affiliations</Table.HeaderCell>
          </Table.Row>
        </Table.Header>

        <Table.Body>
          <Table.Row>
            <Table.Cell>
              <Checkbox label="Natalia (123)" />
            </Table.Cell>
          </Table.Row>
          <Table.Row>
            <Table.Cell>
              <Checkbox label="Marco (321)" />
            </Table.Cell>
          </Table.Row>
          <Table.Row>
            <Table.Cell>
              <Checkbox label="Giota (333)" />
            </Table.Cell>
          </Table.Row>
        </Table.Body>
      </Table>
    </Sidebar>
  );
}

SideBar.propTypes = {
  filterType: PropTypes.string.isRequired,
};
