# CM6 supplied producer and independent join

`ProducerModel(q,d,c,t,q_pin,d_pin,operation)` validates raw context, complete
collection and tables before accepting commands. Its serial model retains exact
input pins; `seal()` yields an immutable supplied terminal when accounting and
footer are complete. `verify_events` parses the event lifecycle independently;
`parse_terminal` validates the supplied snapshot; `join_supplied` reparses and
joins every raw input. All fixture/source/runtime/producer hashes are synthetic
unless supplied under separate authority. These contracts provide no native
producer, execution admission, historical custody or held-debt discharge.
